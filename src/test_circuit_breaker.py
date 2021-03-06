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
    def test_retries_while_conn_timeout(self, mock_client):
        # arrange
        resp501 = Mock()
        resp501.status = 501
        resp408 = Mock()
        resp408.status = 408
        resp200 = Mock()
        resp200.status = 200

        mock_client.getresponse.side_effect = [resp501, resp408, resp501, resp501, resp200]
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
    def test_retries_until_window_timeout(self, mock_client):
        # arrange
        resp501 = Mock()
        resp501.status = 501
        resp408 = Mock()
        resp408.status = 408
        resp200 = Mock()
        resp200.status = 200

        mock_client.getresponse.side_effect = [resp501, resp408, resp501, resp501, resp200]
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
    def test_retries_until_window_timeout(self, mock_client):
        # arrange
        resp501 = Mock()
        resp501.status = 501
        resp200 = Mock()
        resp200.status = 200

        mocked_resps = [resp501 for _ in range(6)]
        mocked_resps.append(resp200)
        mock_client.getresponse.side_effect = mocked_resps
        # mock time.sleep to speedup
        time.sleep = Mock()

        # act
        cb = CircuitBreaker(mock_client, 6, 20)
        # exponential back-off with random fraction: sleep 1, 2, 4, 8, 16
        # timeline: 0 --> sleep(1.1) -- 1.1 --> sleep (2.1) --> 3.2 --> sleep (4.3) --> 7.5 -> sleep (8.6) --> 16.1
        with patch('time.time', side_effect=[0, 1.1, 3.2, 7.5, 16.1, 33.7]):
            with self.assertRaises(CircuitOpenTimeout):
                cb.do_request('GET', '/bah')

        calls = [call('GET', '/bah') for _ in range(4)]
        mock_client.request.assert_has_calls(calls)
        assert 4 == mock_client.request.call_count
