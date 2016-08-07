# Base class that is inherited from to prevent dynamic properties.


class Freezeable(object):
    __is_frozen = False

    def __setattr__(self, key, value):
        if self.__is_frozen and not hasattr(self, key):
            raise AttributeError('The attribute "%s" does not exist.' % key)
        super(Freezeable, self).__setattr__(key, value)

    def _freeze(self):
        self.__is_frozen = True