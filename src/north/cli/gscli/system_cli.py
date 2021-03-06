from .cli import GSObject as Object
from .base import InvalidInput, Completer
from .system import AAA, TACACS, Mgmtif
from prompt_toolkit.document import Document
from prompt_toolkit.completion import WordCompleter, Completion, NestedCompleter
from .common import sysrepo_wrap
import re


class Mgmt_CLI(Object):
    def __init__(self, conn, parent, ifname):
        super().__init__(parent)
        self.session = conn.start_session()
        self.name = ifname
        self.mgmt = Mgmtif(conn)
        self.ip_cmd_list = ["address", "route"]
        self.no_dict = {"ip": {"route": None, "address": None}}
        mgmt_iflist = [
            v["name"] for v in self.mgmt.get_mgmt_interface_list("operational")
        ]
        if len(mgmt_iflist) == 0 or self.name not in mgmt_iflist:
            raise InvalidInput(f"no interface found : {ifname}")

        @self.command(NestedCompleter.from_nested_dict(self.no_dict))
        def no(args):
            if len(args) < 2:
                raise InvalidInput("usage: {}".format(self.no_usage))
            if args[0] == "ip":
                if args[1] == "address":
                    if len(args) != 3:
                        raise InvalidInput("usage: no ip address A.B.C.D/<mask>")
                    try:
                        ip_addr = args[2].split("/")[0]
                        mask = args[2].split("/")[1]
                    except IndexError as error:
                        raise InvalidInput(
                            "Entered address is not in the expected format - A.B.C.D/<mask>"
                        )
                    self.mgmt.set_ip_addr(ifname, ip_addr, mask, False)
                elif args[1] == "route":
                    if len(args) != 3:
                        raise InvalidInput("usage :no ip route <dst_prefix>")
                    dst_prefix = args[2]
                    self.mgmt.set_route(ifname, dst_prefix, False)
            else:
                raise InvalidInput(f"{self.no_usage}")

        @self.command(WordCompleter(self.ip_cmd_list))
        def ip(args):
            if len(args) < 2:
                raise InvalidInput(self.usage())
            if args[0] == "address":
                if len(args) != 2:
                    raise InvalidInput("usage: ip address A.B.C.D/<mask>")
                try:
                    ip_addr = args[1].split("/")[0]
                    mask = args[1].split("/")[1]
                except IndexError as error:
                    raise InvalidInput(
                        "Entered address is not in the expected format - A.B.C.D/<mask>"
                    )
                self.mgmt.set_ip_addr(ifname, ip_addr, mask, True)
            elif args[0] == "route":
                if len(args) != 2:
                    raise InvalidInput("usage :ip route <dst_prefix>")
                dst_prefix = args[1]
                self.mgmt.set_route(ifname, dst_prefix, True)

            else:
                raise InvalidInput(self.usage())

        @self.command(parent.get_completer("show"))
        def show(args):
            if len(args) != 0:
                return parent.show(args)

    def __str__(self):
        return "interface({})".format(self.name)

    def no_usage(self):
        no_keys = list(self.no_dict.keys())
        print(f'usage: no [{"|".join(no_keys)}]')

    def usage(self):
        return "usage:\n ip address A.B.C.D/<mask>\n ip route <dst_prefix>\n"


class AAA_CLI(Object):
    def __init__(self, conn):
        self.session = conn.start_session()
        self.aaa_sys = AAA(conn)

    def aaa(self, args):
        usage = "usage: aaa authentication login default (group tacacs| local)"

        if len(args) != 4 and len(args) != 5:
            raise InvalidInput(usage)
        if args[0] != "authentication" or args[1] != "login" or args[2] != "default":
            raise InvalidInput(usage)
        if len(args) == 4 and args[3] == "local":
            value = args[3]
        elif len(args) == 5 and args[3] == "group" and args[4] == "tacacs":
            value = args[4]
        else:
            raise InvalidInput(usage)
        self.aaa_sys.set_aaa(value)


class TACACS_CLI(Object):
    def __init__(self, conn):
        self.session = conn.start_session()
        self.tacacs = TACACS(conn)

    def tacacs_server(self, args):
        usage = "usage: tacacs-server host (ipaddress) key (string) [port (portnumber)] [timeout (seconds)]"

        if len(args) != 4 and len(args) != 6 and len(args) != 8:
            raise InvalidInput(usage)
        if args[0] != "host" or args[2] != "key":
            raise InvalidInput(usage)

        ipAddress = args[1]
        key = args[3]
        # TODO extract these default values from the YANG model
        port = 49
        timeout = 300

        if len(args) == 6:
            if args[4] != "port" and args[4] != "timeout":
                raise InvalidInput(usage)

            if args[4] == "port":
                port = args[5]
            elif args[4] == "timeout":
                timeout = args[5]

        elif len(args) == 8:
            if args[4] != "port" or args[6] != "timeout":
                raise InvalidInput(usage)

            port = args[5]
            timeout = args[7]

        self.tacacs.set_tacacs_server(ipAddress, key, port, timeout)


class NACM(Object):

    XPATH = "/ietf-netconf-acm:nacm"

    def __init__(self, conn, parent):
        super().__init__(parent)
        self.session = conn.start_session()
        self.sr_op = sysrepo_wrap(self.session)

        @self.command()
        def disable(line):
            if len(line) != 0:
                raise InvalidInput("usage: disable[cr]")
            self.sr_op.set_data(f"{self.XPATH}/enable-nacm", False)

        @self.command()
        def enable(line):
            if len(line) != 0:
                raise InvalidInput("usage: enable[cr]")
            self.sr_op.set_data(f"{self.XPATH}/enable-nacm", True)

    def __str__(self):
        return "nacm"


class Netconf(Object):

    XPATH = "/goldstone-system:system/netconf"

    def __init__(self, conn, parent):
        super().__init__(parent)
        self.session = conn.start_session()
        self.sr_op = sysrepo_wrap(self.session)

        @self.command()
        def shutdown(line):
            if len(line) != 0:
                raise InvalidInput("usage: shutdown[cr]")
            self.sr_op.set_data(f"{self.XPATH}/config/enabled", False)

        @self.command(WordCompleter(["shutdown"]))
        def no(line):
            if len(line) != 1 or line[0] != "shutdown":
                raise InvalidInput("usage: no shutdown")
            self.sr_op.set_data(f"{self.XPATH}/config/enabled", True)

        @self.command()
        def nacm(line):
            if len(line) != 0:
                raise InvalidInput("usage: nacm[cr]")
            return NACM(conn, self)

    def __str__(self):
        return "netconf"


class System(Object):
    def __init__(self, conn, parent):
        super().__init__(parent)

        @self.command(name="netconf")
        def netconf(line):
            if len(line) != 0:
                raise InvalidInput("usage: netconf[cr]")
            return Netconf(conn, self)

    def __str__(self):
        return "system"
