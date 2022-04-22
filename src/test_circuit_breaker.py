from http.client import HTTPConnection
import unittest
from circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitOpenTimeout
from unittest.mock import Mock
from unittest.mock import patch, call
import time


class test_circuitbreaker(unittest.TestCase):

    @patch('http.client.HTTPConnection')
    def test_retries_until_successful(self, mock_client):
        # arrange
        resp500 = Mock()
        resp500.status = 500
        resp503 = Mock()
        resp503.status = 503
        resp200 = Mock()
        resp200.status = 200

        mock_client.getresponse.side_effect = [resp500, resp503, resp200]
        # mock time.sleep to speedup
        time.sleep = Mock()

        # act
        cb = CircuitBreaker(mock_client, 4, 20)
        actual_resp = cb.do_request('GET', '/foo')

        # assert
        calls = [call('GET', '/foo') for _ in range(3)]
        mock_client.request.assert_has_calls(calls)
        assert 3 == mock_client.request.call_count
        assert actual_resp == resp200

    @patch('http.client.HTTPConnection')
    def test_retries_until_limit(self, mock_client):
        # arrange
        resp501 = Mock()
        resp501.status = 501
        resp200 = Mock()
        resp200.status = 200

        mocked_resps = [resp501 for _ in range(5)]
        mocked_resps.append(resp200)
        mock_client.getresponse.side_effect = mocked_resps
        # mock time.sleep to speedup
        time.sleep = Mock()

        # act
        cb = CircuitBreaker(mock_client, 4, 20)
        with self.assertRaises(CircuitOpenError):
            cb.do_request('GET', '/bah')

        # assert
        calls = [call('GET', '/bah') for _ in range(4)]
        mock_client.request.assert_has_calls(calls)
        assert 4 == mock_client.request.call_count

    @patch('http.client.HTTPConnection')
    def test_retries_until_timeout(self, mock_client):
        # arrange
        resp501 = Mock()
        resp501.status = 501
        resp200 = Mock()
        resp200.status = 200

        mocked_resps = [resp501 for _ in range(5)]
        mocked_resps.append(resp200)
        mock_client.getresponse.side_effect = mocked_resps

        # act
        cb = CircuitBreaker(mock_client, 6, 20)

        # patch time.times() so each round took 10s to complete
        with patch('time.time', side_effect=[1, 11, 21, 31]):
            with self.assertRaises(CircuitOpenTimeout):
                cb.do_request('GET', '/bah')

        # assert: timeout after 20s, i.e. 2 times retries
        calls = [call('GET', '/bah') for _ in range(2)]
        mock_client.request.assert_has_calls(calls)
        assert 2 == mock_client.request.call_count
