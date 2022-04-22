from http.client import HTTPResponse
import random
import time

# Default back-off time
back_off_in_seconds = 1
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
            # Only retries upon 5xx or REQUEST_TIMEOUT (408)
            if resp.status < 500 and resp.status != 408:
                # flow normally
                return resp

            counter += 1
            self.back_off(counter, start_time)
        raise CircuitOpenError

    def back_off(self, counter, start_time):
        """ Sleep backoff exponentially of the counter """
        sleep_time = (back_off_in_seconds * 2 ** (counter - 1)+ random.uniform(0, 1))
        # print("Sleep : %.2fs" % sleep_time)
        
        ellapsed_time = time.time() - start_time
        # print(ellapsed_time)
        if ellapsed_time + sleep_time > self.time_window:
            raise CircuitOpenTimeout

        time.sleep(sleep_time)


# if __name__ == "__main__":
#     breaker = CircuitBreaker(stub_client, 3, 20)
