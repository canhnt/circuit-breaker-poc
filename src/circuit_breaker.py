from http import HTTPStatus
from http.client import HTTPConnection, HTTPResponse
from multiprocessing import Pool
import time

# static delay in seconds after failure
SLEEP_TIME = 2

class CircuitOpenTimeout(Exception):
    """ Exception when the circuit got timeout. """
    pass

class CircuitOpenError(Exception):
    """ Exception when the circuit exceeded maximal error threshold. """
    pass

class CircuitBreaker:
    """ A circuit breaker wrapper utility to handle retries upon errors or timeout. """

    def __init__(self, http_client, error_threshold: int, time_window: int):
        self.http_client = http_client
        self.error_threshold = error_threshold
        self.time_window = time_window

    def do_request(self, method: str, path: str) -> HTTPResponse:
        """ Execute request with circuit breaker config"""
        counter = 0
        
        start_time = time.time()
        while counter < self.error_threshold:
            self.http_client.request(method, path)
            resp = self.http_client.getresponse()
            if 200 <= resp.status < 400:
                # flow normally
                return resp
            
            ellapsed_time = time.time() - start_time
            # print(ellapsed_time)
            if ellapsed_time > self.time_window - SLEEP_TIME:
                raise CircuitOpenTimeout
            
            counter += 1
            time.sleep(SLEEP_TIME)
        raise CircuitOpenError


# if __name__ == "__main__":
#     breaker = CircuitBreaker(stub_client, 3, 20)
