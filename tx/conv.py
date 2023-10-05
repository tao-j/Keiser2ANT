def uint8(val):
    return int(val) & 0xFF


def uint16(val):
    return int(val) & 0xFFFF


def uint32(val):
    return int(val) & 0xFFFFFFFF


class BLEConv:
    def __init__(self, data_src) -> None:
        self.data_src = data_src

    def get_wr(self):
        return uint32(self.data_src.wr)

    def get_cr(self):
        return uint16(self.data_src.cr)

    def get_wev(self):
        return uint16(self.data_src.wev)

    def get_cev(self):
        return uint16(self.data_src.cev)

    def get_power(self):
        return uint16(self.data_src.power)


class ANTConv:
    def __init__(self, data_src) -> None:
        self.data_src = data_src

    def get_event_count(self):
        return uint8(self.data_src.power_event_counts)

    def get_cum_power(self):
        return uint16(self.data_src.cum_power)

    def get_cadence(self):
        return uint8(self.data_src.cadence)

    def get_power(self):
        return uint16(self.data_src.power)

    def get_cum_rev_count(self):
        return uint16(self.data_src.wr)

    def get_event_time_ms(self):
        return uint16(self.data_src.wev)
