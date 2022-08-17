
default_config = {
    "time_to_wait_for_polling": 10.0,
}


class ConfigObject:
    def __init__(self, **argv):
        self.__dict__.update(argv)


global_config = ConfigObject(**default_config)

