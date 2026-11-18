class AppError(Exception):
    # The base class for all of OUR errors. Inherits from Exception, like a custom
    # exception class in C# deriving from System.Exception.

    status_code: int = 500
    detail: str = "Internal error"
    # Class-level defaults. Each subclass overrides these, the way a derived
    # class in C# overrides a virtual property.

    def __init__(self, detail: str | None = None):
        # The constructor. detail is optional: pass one to override the default message.

        if detail is not None:
            self.detail = detail
            # Store a custom message on this instance. Instance attributes take
            # priority over the class-level default when you read self.detail.

        super().__init__(self.detail)
        # Call the base Exception constructor with the message, like
        # `: base(message)` in C#, so str(error) and logs show it.


class UnsupportedCurrencyError(AppError):
    status_code = 400
    # The client's fault: they asked for a currency that doesn't exist.

    def __init__(self, currency: str):
        super().__init__(f"Unsupported currency: {currency}")
        # Build a specific message that includes the bad code, then pass it
        # up to AppError's constructor.


class RateServiceUnavailableError(AppError):
    status_code = 503
    detail = "Exchange rate service unavailable, please try again later"
    # No __init__ needed: it inherits AppError's, and the defaults are enough.


class RateServiceTimeoutError(AppError):
    status_code = 504
    detail = "Exchange rate service timed out"


class RateServiceBadResponseError(AppError):
    status_code = 502
    detail = "Exchange rate service returned an error"
