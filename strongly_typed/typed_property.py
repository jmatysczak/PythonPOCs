# Decorator that is used to make properties strongly typed.


from functools import wraps


def typed_property(required_type):
    def typed_property_decorator(func):
        @wraps(func)
        def typed_property_wrapper(self, value):
            if not isinstance(value, required_type):
                raise TypeError("The value %s must of type %s" % (value, required_type))
            return func(self, value)

        return typed_property_wrapper

    return typed_property_decorator