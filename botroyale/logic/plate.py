"""Home of `Plate`."""
from typing import Any, Optional
import copy
from botroyale.util.hexagon import Hexagon, Hex
from botroyale.logic import PlateType


class Plate(Hexagon):
    """Pressure Plate.

    Plates will be equal to and hash like all other instances of
    `botroyale.util.hexagon.Hexagon` subclasses if their cube is equal.
    """

    def __init__(
        self,
        cube: tuple[int, int, int],
        plate_type: PlateType,
        pressure: int,
        min_pressure: Optional[int] = None,
        pressure_reset: bool = False,
        targets: Optional[set[Hexagon]] = None,
    ):
        """Initialize the class.

        Args:
            cube: The cube of the `botroyale.util.hexagon.Hexagon`
            plate_type: One of `botroyale.logic.PlateType`
            pressure: Negative integer
            min_pressure: Negative integer
            pressure_reset: If the pressure resets after popping
            targets: A set of `botroyale.util.hexagon.Hexagon` that the plate targets
        """
        super().__init__(*cube)
        self.plate_type: PlateType = plate_type
        assert pressure < 0
        self.pressure: int = pressure
        if min_pressure is None:
            min_pressure = pressure
        assert min_pressure < 0
        self.min_pressure: int = min_pressure
        self.pressure_reset: bool = pressure_reset
        if targets is None:
            targets = set()
        self.targets: set[Hexagon] = targets

    def with_new_hex(self, hex: Hexagon) -> "Plate":
        """Create an identical `Plate` but with a different *hex*."""
        return self._with_new_hex(hex, self)

    @classmethod
    def _with_new_hex(cls, hex: Hexagon, plate: "Plate") -> "Plate":
        """Create an identical `Plate` to *plate* but with a different *hex*."""
        return cls(
            hex.cube,
            plate_type=plate.plate_type,
            pressure=plate.pressure,
            min_pressure=plate.min_pressure,
            pressure_reset=plate.pressure_reset,
            targets=copy.copy(plate.targets),
        )

    def export(self) -> dict:
        """Export plate data to serializable dictionary."""
        return {
            "xy": self.xy,
            "plate_type": self.plate_type.name,
            "min_pressure": self.min_pressure,
            "pressure": self.pressure,
            "pressure_reset": self.pressure_reset,
            "targets": [h.xy for h in self.targets],
        }

    @classmethod
    def from_exported(cls, data: dict) -> "Plate":
        """Get a Plate from `Plate.export` dictionary."""
        plate_type = getattr(PlateType, data["plate_type"])
        hex = Hex(*data["xy"])
        targets = {Hex(*xy) for xy in data["targets"]}
        return cls(
            cube=hex.cube,
            plate_type=plate_type,
            min_pressure=data["min_pressure"],
            pressure=data["pressure"],
            pressure_reset=data["pressure_reset"],
            targets=targets,
        )

    def __eq__(self, other: Any) -> bool:
        """Equality."""
        if isinstance(other, Hexagon):
            return self.cube == other.cube
        return False

    def __hash__(self):
        """Hash."""
        return hash(self.cube)

    def __repr__(self):
        """Repr."""
        return f"<Plate {self.xy} {self.plate_type.name}>"
