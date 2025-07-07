import threading

def debounce(wait):
    """ Decorator that will postpone a functions' execution until after `wait` seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        timer = None
        def debounced(*args, **kwargs):
            nonlocal timer
            def call_it():
                fn(*args, **kwargs)

            if timer is not None:
                timer.cancel()

            timer = threading.Timer(wait, call_it)
            timer.start()

        return debounced
    return decorator
