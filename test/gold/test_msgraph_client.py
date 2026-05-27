##
## Created : Sun May 25 09:00:00 PDT 2026
## SPDX-FileCopyrightText: 2014-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
## ####
##
## Unit tests for the Microsoft Graph API client module.
## Uses unittest.mock to avoid real HTTP calls.
##

import json, os, sys, unittest
from unittest.mock import MagicMock, patch, PropertyMock

## Ensure the asynk package is importable
asynk_base = os.path.dirname(os.path.dirname(os.path.dirname(
                 os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(asynk_base, 'asynk'))

from msgraph_client import (GraphAuthProvider, GraphContactsClient,
                             GraphAPIError, GraphAuthError,
                             DeltaSyncResult, GRAPH_BASE_URL)


class MockAuthProvider:
    """A mock auth provider that returns a fake token without real OAuth."""

    def __init__ (self):
        self._access_token = 'mock_access_token_12345'

    def authenticate (self):
        return self._access_token

    def get_headers (self):
        return {
            'Authorization'  : 'Bearer %s' % self._access_token,
            'Content-Type'   : 'application/json',
        }


def _make_response (status_code=200, json_data=None, headers=None):
    """Create a mock requests.Response object."""

    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.json.return_value = json_data or {}
    resp.text = json.dumps(json_data or {})
    return resp


class TestGraphContactsClientFolders(unittest.TestCase):
    """Tests for contact folder operations."""

    def setUp (self):
        self.auth = MockAuthProvider()
        self.client = GraphContactsClient(self.auth)

    @patch.object(GraphContactsClient, '_paginate')
    def test_list_contact_folders (self, mock_paginate):
        mock_paginate.return_value = iter([
            {'id': 'f1', 'displayName': 'Contacts'},
            {'id': 'f2', 'displayName': 'My Folder'},
        ])

        folders = self.client.list_contact_folders()
        self.assertEqual(len(folders), 2)
        self.assertEqual(folders[0]['displayName'], 'Contacts')
        self.assertEqual(folders[1]['id'], 'f2')
        mock_paginate.assert_called_once_with('/me/contactFolders')

    @patch.object(GraphContactsClient, '_request')
    def test_create_contact_folder (self, mock_request):
        mock_request.return_value = {'id': 'new_f', 'displayName': 'Test'}
        result = self.client.create_contact_folder('Test')

        mock_request.assert_called_once_with(
            'POST', '/me/contactFolders',
            json={'displayName': 'Test'})
        self.assertEqual(result['id'], 'new_f')

    @patch.object(GraphContactsClient, '_request')
    def test_delete_contact_folder (self, mock_request):
        mock_request.return_value = None
        self.client.delete_contact_folder('f1')
        mock_request.assert_called_once_with(
            'DELETE', '/me/contactFolders/f1')


class TestGraphContactsClientContacts(unittest.TestCase):
    """Tests for contact CRUD operations."""

    def setUp (self):
        self.auth = MockAuthProvider()
        self.client = GraphContactsClient(self.auth)

    @patch.object(GraphContactsClient, '_paginate')
    def test_list_contacts_default_folder (self, mock_paginate):
        mock_paginate.return_value = iter([
            {'id': 'c1', 'givenName': 'Alice'},
        ])

        contacts = self.client.list_contacts()
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]['givenName'], 'Alice')

        ## Verify the call used /me/contacts (no folder)
        call_args = mock_paginate.call_args
        self.assertEqual(call_args[0][0], '/me/contacts')

    @patch.object(GraphContactsClient, '_paginate')
    def test_list_contacts_specific_folder (self, mock_paginate):
        mock_paginate.return_value = iter([])
        self.client.list_contacts(folder_id='f1')

        call_args = mock_paginate.call_args
        self.assertEqual(call_args[0][0], '/me/contactFolders/f1/contacts')

    @patch.object(GraphContactsClient, '_request')
    def test_get_contact (self, mock_request):
        mock_request.return_value = {'id': 'c1', 'givenName': 'Bob'}
        result = self.client.get_contact('c1')

        self.assertEqual(result['givenName'], 'Bob')
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], 'GET')
        self.assertEqual(call_args[0][1], '/me/contacts/c1')

    @patch.object(GraphContactsClient, '_request')
    def test_create_contact (self, mock_request):
        contact = {'givenName': 'Charlie', 'surname': 'Brown'}
        mock_request.return_value = {'id': 'c_new', **contact}

        result = self.client.create_contact('f1', contact)
        self.assertEqual(result['id'], 'c_new')
        mock_request.assert_called_once_with(
            'POST', '/me/contactFolders/f1/contacts', json=contact)

    @patch.object(GraphContactsClient, '_request')
    def test_update_contact (self, mock_request):
        patch_data = {'givenName': 'Charlie-Updated'}
        mock_request.return_value = {'id': 'c1', **patch_data}

        result = self.client.update_contact('c1', patch_data)
        self.assertEqual(result['givenName'], 'Charlie-Updated')
        mock_request.assert_called_once_with(
            'PATCH', '/me/contacts/c1', json=patch_data)

    @patch.object(GraphContactsClient, '_request')
    def test_delete_contact (self, mock_request):
        mock_request.return_value = None
        self.client.delete_contact('c1')
        mock_request.assert_called_once_with(
            'DELETE', '/me/contacts/c1')


class TestGraphContactsClientBatch(unittest.TestCase):
    """Tests for batch operations."""

    def setUp (self):
        self.auth = MockAuthProvider()
        self.client = GraphContactsClient(self.auth)

    @patch.object(GraphContactsClient, '_batch')
    def test_get_contacts_batch (self, mock_batch):
        mock_batch.return_value = [
            {'id': '0', 'status': 200,
             'body': {'id': 'c1', 'givenName': 'Alice'}},
            {'id': '1', 'status': 200,
             'body': {'id': 'c2', 'givenName': 'Bob'}},
        ]

        results = self.client.get_contacts(['c1', 'c2'])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['givenName'], 'Alice')
        self.assertEqual(results[1]['givenName'], 'Bob')

    @patch.object(GraphContactsClient, '_batch')
    def test_get_contacts_partial_failure (self, mock_batch):
        mock_batch.return_value = [
            {'id': '0', 'status': 200,
             'body': {'id': 'c1', 'givenName': 'Alice'}},
            {'id': '1', 'status': 404,
             'body': {'error': {'code': 'ItemNotFound'}}},
        ]

        results = self.client.get_contacts(['c1', 'c2'])
        ## Only the successful one should be in results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['givenName'], 'Alice')

    @patch.object(GraphContactsClient, '_batch')
    def test_create_contacts_batch (self, mock_batch):
        mock_batch.return_value = [
            {'id': '0', 'status': 201,
             'body': {'id': 'new1', 'givenName': 'Alice'}},
            {'id': '1', 'status': 201,
             'body': {'id': 'new2', 'givenName': 'Bob'}},
        ]

        contacts = [{'givenName': 'Alice'}, {'givenName': 'Bob'}]
        results = self.client.create_contacts('f1', contacts)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], 'new1')
        self.assertEqual(results[1]['id'], 'new2')

    @patch.object(GraphContactsClient, '_batch')
    def test_update_contacts_batch (self, mock_batch):
        mock_batch.return_value = [
            {'id': '0', 'status': 200,
             'body': {'id': 'c1', 'givenName': 'Alice-Updated'}},
        ]

        updates = [('c1', {'givenName': 'Alice-Updated'})]
        results = self.client.update_contacts(updates)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['givenName'], 'Alice-Updated')

    @patch.object(GraphContactsClient, '_batch')
    def test_delete_contacts_batch (self, mock_batch):
        mock_batch.return_value = [
            {'id': '0', 'status': 204, 'body': {}},
            {'id': '1', 'status': 204, 'body': {}},
        ]

        ## Should not raise
        self.client.delete_contacts(['c1', 'c2'])
        mock_batch.assert_called_once()

    def test_empty_batch_operations (self):
        """Batch operations with empty inputs should return immediately."""

        self.assertEqual(self.client.get_contacts([]), [])
        self.assertEqual(self.client.create_contacts('f1', []), [])
        self.assertEqual(self.client.update_contacts([]), [])
        self.assertIsNone(self.client.delete_contacts([]))


class TestGraphContactsClientDeltaSync(unittest.TestCase):
    """Tests for delta sync operations."""

    def setUp (self):
        self.auth = MockAuthProvider()
        self.client = GraphContactsClient(self.auth)

    @patch('requests.Session.get')
    def test_initial_delta_sync (self, mock_get):
        """First delta sync should return all contacts."""

        mock_get.return_value = _make_response(200, {
            'value': [
                {'id': 'c1', 'givenName': 'Alice'},
                {'id': 'c2', 'givenName': 'Bob'},
            ],
            '@odata.deltaLink': 'https://graph.microsoft.com/delta?token=abc',
        })

        result = self.client.delta_sync('folder1')
        self.assertIsInstance(result, DeltaSyncResult)
        self.assertEqual(len(result.changed), 2)
        self.assertEqual(len(result.deleted), 0)
        self.assertEqual(result.delta_link,
                         'https://graph.microsoft.com/delta?token=abc')

    @patch('requests.Session.get')
    def test_delta_sync_with_changes (self, mock_get):
        """Subsequent delta sync with modifications and deletions."""

        mock_get.return_value = _make_response(200, {
            'value': [
                {'id': 'c1', 'givenName': 'Alice-Updated'},
                {'id': 'c3', '@removed': {'reason': 'deleted'}},
            ],
            '@odata.deltaLink': 'https://graph.microsoft.com/delta?token=def',
        })

        result = self.client.delta_sync(
            'folder1',
            delta_link='https://graph.microsoft.com/delta?token=abc')

        self.assertEqual(len(result.changed), 1)
        self.assertEqual(result.changed[0]['givenName'], 'Alice-Updated')
        self.assertEqual(len(result.deleted), 1)
        self.assertEqual(result.deleted[0], 'c3')

    @patch('requests.Session.get')
    def test_delta_sync_pagination (self, mock_get):
        """Delta sync should follow @odata.nextLink for pagination."""

        page1 = _make_response(200, {
            'value': [{'id': 'c1', 'givenName': 'Alice'}],
            '@odata.nextLink': 'https://graph.microsoft.com/delta?skip=1',
        })
        page2 = _make_response(200, {
            'value': [{'id': 'c2', 'givenName': 'Bob'}],
            '@odata.deltaLink': 'https://graph.microsoft.com/delta?token=xyz',
        })
        mock_get.side_effect = [page1, page2]

        result = self.client.delta_sync('folder1')
        self.assertEqual(len(result.changed), 2)
        self.assertEqual(mock_get.call_count, 2)


class TestGraphContactsClientExtensions(unittest.TestCase):
    """Tests for open extension operations."""

    def setUp (self):
        self.auth = MockAuthProvider()
        self.client = GraphContactsClient(self.auth)

    @patch.object(GraphContactsClient, '_request')
    def test_get_extension_found (self, mock_request):
        mock_request.return_value = {
            'extensionName': 'com.asynk.syncdata',
            'syncTags': {'profile1': 'remote_id'},
        }

        result = self.client.get_extension('c1', 'com.asynk.syncdata')
        self.assertIsNotNone(result)
        self.assertEqual(result['syncTags']['profile1'], 'remote_id')

    @patch.object(GraphContactsClient, '_request')
    def test_get_extension_not_found (self, mock_request):
        mock_request.side_effect = GraphAPIError(404, 'ErrorItemNotFound',
                                                  'Not found')

        result = self.client.get_extension('c1', 'com.asynk.syncdata')
        self.assertIsNone(result)

    @patch.object(GraphContactsClient, '_request')
    def test_set_extension_update_existing (self, mock_request):
        """If extension exists, PATCH should succeed."""

        mock_request.side_effect = [
            {'extensionName': 'com.asynk.syncdata', 'syncTags': '{"profile1": "updated_id"}'},
            {'extensionName': 'com.asynk.syncdata', 'syncTags': '{"profile1": "updated_id"}'},
        ]

        data = {'syncTags': {'profile1': 'updated_id'}}
        result = self.client.set_extension('c1', 'com.asynk.syncdata', data)
        self.assertIsNotNone(result)

        ## First call should be GET (check existence), second should be PATCH
        self.assertEqual(mock_request.call_count, 2)
        first_call = mock_request.call_args_list[0]
        self.assertEqual(first_call[0][0], 'GET')
        second_call = mock_request.call_args_list[1]
        self.assertEqual(second_call[0][0], 'PATCH')

    @patch.object(GraphContactsClient, '_request')
    def test_set_extension_create_new (self, mock_request):
        """If GET returns 404, should fall back to POST."""

        mock_request.side_effect = [
            GraphAPIError(404, 'ErrorItemNotFound', 'Not found'),
            {'extensionName': 'com.asynk.syncdata', 'newKey': 'newVal'},
        ]

        data = {'newKey': 'newVal'}
        result = self.client.set_extension('c1', 'com.asynk.syncdata', data)
        self.assertIsNotNone(result)

        ## Should have been called twice: GET (failed) then POST
        self.assertEqual(mock_request.call_count, 2)
        first_call = mock_request.call_args_list[0]
        self.assertEqual(first_call[0][0], 'GET')
        second_call = mock_request.call_args_list[1]
        self.assertEqual(second_call[0][0], 'POST')


class TestGraphContactsClientRetry(unittest.TestCase):
    """Tests for throttling and retry behavior."""

    def setUp (self):
        self.auth = MockAuthProvider()
        self.client = GraphContactsClient(self.auth)

    @patch('time.sleep')
    @patch('requests.Session.request')
    def test_retry_on_429 (self, mock_request, mock_sleep):
        """Should retry after Retry-After on 429."""

        throttled = _make_response(429, {'error': {'message': 'throttled'}},
                                   headers={'Retry-After': '1'})
        success   = _make_response(200, {'id': 'c1', 'givenName': 'Alice'})
        mock_request.side_effect = [throttled, success]

        result = self.client._request('GET', '/me/contacts/c1')
        self.assertEqual(result['givenName'], 'Alice')
        self.assertEqual(mock_request.call_count, 2)
        mock_sleep.assert_called_once_with(1)

    @patch('time.sleep')
    @patch('requests.Session.request')
    def test_retry_on_503 (self, mock_request, mock_sleep):
        """Should retry with backoff on 503."""

        error503 = _make_response(503, {'error': {'message': 'unavailable'}})
        success  = _make_response(200, {'id': 'c1'})
        mock_request.side_effect = [error503, success]

        result = self.client._request('GET', '/me/contacts/c1')
        self.assertEqual(result['id'], 'c1')
        self.assertEqual(mock_request.call_count, 2)

    @patch('time.sleep')
    @patch('requests.Session.request')
    def test_error_on_400 (self, mock_request, mock_sleep):
        """Should raise GraphAPIError on 400 without retry."""

        error400 = _make_response(400, {
            'error': {'code': 'BadRequest', 'message': 'Invalid data'}
        })
        mock_request.return_value = error400

        with self.assertRaises(GraphAPIError) as ctx:
            self.client._request('POST', '/me/contacts', json={})

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.error_code, 'BadRequest')
        ## Should NOT retry — only one call
        self.assertEqual(mock_request.call_count, 1)


class TestGraphContactsClientPagination(unittest.TestCase):
    """Tests for the _paginate helper."""

    def setUp (self):
        self.auth = MockAuthProvider()
        self.client = GraphContactsClient(self.auth)

    @patch('requests.Session.get')
    def test_paginate_single_page (self, mock_get):
        mock_get.return_value = _make_response(200, {
            'value': [{'id': 'c1'}, {'id': 'c2'}],
        })

        items = list(self.client._paginate('/me/contacts'))
        self.assertEqual(len(items), 2)
        self.assertEqual(mock_get.call_count, 1)

    @patch('requests.Session.get')
    def test_paginate_multi_page (self, mock_get):
        page1 = _make_response(200, {
            'value': [{'id': 'c1'}],
            '@odata.nextLink': GRAPH_BASE_URL + '/me/contacts?$skip=1',
        })
        page2 = _make_response(200, {
            'value': [{'id': 'c2'}],
        })
        mock_get.side_effect = [page1, page2]

        items = list(self.client._paginate('/me/contacts'))
        self.assertEqual(len(items), 2)
        self.assertEqual(mock_get.call_count, 2)


class TestBatchChunking(unittest.TestCase):
    """Tests that batch operations correctly chunk large request lists."""

    def setUp (self):
        self.auth = MockAuthProvider()
        self.client = GraphContactsClient(self.auth)

    @patch.object(GraphContactsClient, '_request')
    def test_batch_chunking (self, mock_request):
        """25 requests should be chunked into 2 batches (20 + 5)."""

        ## Mock _request to return batch responses
        def side_effect (method, path, json=None, **kwargs):
            if method == 'POST' and path == '/$batch':
                n = len(json['requests'])
                return {
                    'responses': [{'id': str(i), 'status': 200, 'body': {}}
                                  for i in range(n)]
                }
            return {}

        mock_request.side_effect = side_effect

        reqs = [{'id': str(i), 'method': 'GET',
                 'url': '/me/contacts/c%d' % i}
                for i in range(25)]

        responses = self.client._batch(reqs)
        self.assertEqual(len(responses), 25)

        ## _request should have been called twice (2 batch chunks)
        self.assertEqual(mock_request.call_count, 2)

        ## First chunk should have 20 requests
        first_call = mock_request.call_args_list[0]
        self.assertEqual(len(first_call[1]['json']['requests']), 20)

        ## Second chunk should have 5 requests
        second_call = mock_request.call_args_list[1]
        self.assertEqual(len(second_call[1]['json']['requests']), 5)


class TestDeltaSyncResult(unittest.TestCase):
    """Tests for the DeltaSyncResult data class."""

    def test_construction (self):
        result = DeltaSyncResult(
            changed=[{'id': 'c1'}],
            deleted=['c2'],
            delta_link='https://example.com/delta?token=abc')

        self.assertEqual(len(result.changed), 1)
        self.assertEqual(len(result.deleted), 1)
        self.assertEqual(result.delta_link,
                         'https://example.com/delta?token=abc')


if __name__ == '__main__':
    unittest.main()
