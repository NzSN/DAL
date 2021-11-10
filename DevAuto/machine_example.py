"""
This file provide an example of how to make a more concrete macine
from Machine within DevCore.
"""

import DevAuto.Core as core
import DevAuto.Core.devCoreTypes as da_typ


###############################################################################
#                                TrivialMachine                               #
###############################################################################
class TrivialMachine(core.Machine):
    """
    A machine without properties, operations, it's trivial.
    """

    def __init__(self) -> None:
        core.Machine.__init__(self, "Trivial", [], [])


###############################################################################
#                  BoxMachine, a machine that simulate a box                  #
###############################################################################
# Box Properties
boxProperties = [
    core.Property("contain", 10)
]

boxOpSpec = [
    # Open
    core.OpSpec("open", (), ("N/A", da_typ.DNone)),
    # Close
    core.OpSpec("close", (), ("N/A", da_typ.DNone)),
    # Put
    core.OpSpec("put", (("Candy", da_typ.DSTR)), ("N/A", da_typ.DNone)),
    # Get
    core.OpSpec("get", (), ("Candy", da_typ.DSTR))
]


class BoxMachine(core.Machine):
    """
    A machine that can open and close, just like a box.
    """

    def __init__(self) -> None:
        core.Machine.__init__(self, "Box", boxProperties, boxOpSpec)

    @core.Machine.Operation
    def open(self) -> core.DNone:
        return self.operate(
            core.Operation(
                "core",
                "Box",
                core.opTuple("open", [])
            )
        )

    @core.Machine.Operation
    def close(self) -> core.DNone:
        return self.operate(
            core.Operation(
                "core",
                "Box",
                core.opTuple("close", [])
            )
        )

    @core.Machine.Operation
    def put(self, candy: str) -> core.DNone:
        arg = core.DStr(candy)

        return self.operate(
            "core", "Box",
            core.opTuple("put", [arg])
        )

    @core.Machine.Operation
    def get(self) -> core.DStr:
        return self.operate(
            "core", "Box",
            core.opTuple("get", [])
        )


###############################################################################
#                      Network Device with four interface                     #
###############################################################################
NA = "N/A"
NDProp = [
    core.Property("Interface",
                  "interface-0/1", "interface-0/2",
                  "interface-0/3", "interface-0/4"),
    core.Property("Interface-State", {
        "interface-0/1": NA,
        "interface-0/2": NA,
        "interface-0/3": NA,
        "interface-0/4": NA
    })
]

NDOP = [
    # Startup
    core.OpSpec("startup", (), None),
    # Shutdown
    core.OpSpec("shutdown", (), None),
    # SendEth
    core.OpSpec("send", (("Package", bytes), ("port", str)), None),
    # routeTbl
    core.OpSpec("routeTbl", (), None)
]


class NetDevice(core.Machine):

    def __init__(self) -> None:
        core.Machine.__init__(self, "ND", NDProp, NDOP)

    @core.Machine.Operation
    def startup(self) -> core.Operation:
        return core.Operation("core", "ND", core.opTuple("startup", None))

    @core.Machine.Operation
    def shutdown(self) -> core.Operation:
        return core.Operation("core", "ND", core.opTuple("shutdown", None))

    @core.Machine.Operation("core", "ND", "send")
    def send(self, package: bytes, port: int) -> core.Operation:
        return core.Operation(
            "core", "ND", core.opTuple("send", [package, port]))

    @core.Machine.Operation
    def routeTbl(self) -> da_typ.DA_DICT:
        query = core.Query("core", "ND", ("route", None, da_typ.DA_DICT))
        return self.operate(query)
