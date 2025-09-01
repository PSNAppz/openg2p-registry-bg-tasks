from typing import Optional

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import BigInteger, Date, Integer, String
from sqlalchemy.orm import mapped_column


class G2PRegistryVehicleOwnership(BaseORMModel):
    __tablename__ = "g2p_registry_vehicle_ownership"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_registration_id = mapped_column(String, nullable=False)
    individual_registry_id = mapped_column(Integer, nullable=False)
    individual_unique_id = mapped_column(String, nullable=True)
    owner_aadhaar = mapped_column(String, nullable=True)
    family_registry_id = mapped_column(Integer, nullable=True)
    family_unique_id = mapped_column(String, nullable=True)
    class_of_vehicle = mapped_column(String, nullable=True)
    registration_from_date = mapped_column(Date, nullable=True)
    registration_to_date = mapped_column(Date, nullable=True)
    engine_no = mapped_column(String, nullable=True)
    chassis_no = mapped_column(String, nullable=True)
    manufacturer = mapped_column(String, nullable=True)
    unique_id = mapped_column(String, nullable=True)
    no_of_wheels = mapped_column(BigInteger, nullable=True)

    # Hardcoded mapping of Class of Vehicle (COV) to number of wheels
    COV_TO_WHEELS_MAPPING = {
        "Adapted Vehicle": 4,
        "Ambulance": 4,
        "Animal Ambulances": 4,
        "Articulated Vehicles": 18,  # Truck with multiple axles
        "Auto Rickshaw": 3,
        "Auto Rikckshaw Private": 3,
        "Auxillary Trailer": 2,
        "Break down Van": 4,
        "Bull Dozer": 4,  # Tracked vehicles treated as 4 wheels equivalent
        "Campers Vans": 4,
        "Campers Vans for Private Use": 4,
        "Camper Trailer For Hire": 2,
        "Camper Trailer For Private Use": 2,
        "Camper Vans For Hire": 4,
        "Cash Vans": 4,
        "Chassis Non-Transport": 4,
        "Chassis Transport": 4,
        "COMPRESSOR  MOUNTED": 4,
        "Construction Equipment vehicle for Commercial Use": 4,
        "Contract Carriage": 4,
        "Crane For Commercial Use": 6,  # Usually heavy duty with multiple axles
        "Crane For Private Use": 4,
        "Crane Mounted": 6,
        "Dumper": 6,  # Usually heavy duty trucks
        "Dumper/Excavator": 4,
        "Dumper/Excavator For Private use": 4,
        "Dumper For Private Use": 4,
        "eCart": 3,  # Electric three-wheeler
        "Education Institute Bus": 6,  # Large buses
        "eRickshaw": 3,
        "Excavator For Private Use": 4,
        "Fire Fighting Vehicles": 6,
        "Fire Tenders": 6,
        "Five Wheeler Goods Vehicle": 5,
        "Fork Lift": 4,
        "Generator Mounted": 4,
        "Goods Carriage": 6,  # Usually trucks
        "Goods Carriage for Carrying Animals": 6,
        "Hearses": 4,
        "Imported Motor Car": 4,
        "Imported Motor Cycle": 2,
        "Invalid Carriage": 3,  # Usually tricycle-like
        "Jeep": 4,
        "Library Vans": 4,
        "Loader": 4,
        "Luxory Tourist Cab": 4,
        "Mail Carrier": 4,
        "Maxi Cab": 4,
        "MCRN": 2,  # Motorcycle
        "MC WithTrailer to Carry Personnel Effects": 2,
        "Mobile Canteens": 4,
        "Mobile Clinic": 4,
        "Mobile Satellite Van With Dish Antenna": 4,
        "Mobile Work Shop": 4,
        "Mopeds and Motorised Cycle": 2,
        "Motor Cab": 4,
        "MOTOR CAR": 4,
        "Motor Cycle": 2,
        "MOTOR CYCLE": 2,
        "Motor Cycle for Hire": 2,
        "Motor Cycle With Side Car": 3,
        "Motor Cycle with Trailer To Carry Goods": 2,
        "MOTOR GRADER": 4,
        "NULL": None,  # Unknown/undefined
        "Ominibus": 6,  # Large buses
        "Omnibus for Private Use": 6,
        "Other Vehicle": 4,  # Default assumption
        "Power Tiller": 2,  # Usually two-wheeled agricultural equipment
        "Private Service Vehicle": 4,
        "Quadracycle NonTransport": 4,
        "Quadracycle Transport": 4,
        "Recovery Vehicle": 6,  # Usually heavy duty
        "Rig Mounted": 6,  # Heavy equipment
        "Road Roller": 4,
        "Self Loading Concrete Mixer": 6,  # Heavy trucks
        "SELF PROPELLED HARVESTER": 4,
        "Semi Luxory Tourist Cab": 4,
        "Snorted Laddres": 6,  # Ladder trucks
        "Stage Carriages": 6,  # Buses
        "Station Wagon": 4,
        "Station Wagon for Private Use": 4,
        "Three Wheeled Goods Vehicle": 3,
        "Three Wheeled Vehicles for Personnel Use": 3,
        "Tourist Vehicle": 4,
        "Tower Wagon": 6,  # Heavy utility vehicles
        "Tow Trucks": 6,
        "Tractor Driven Combined Harvester": 4,
        "Tractor for Agricultural Purpose": 4,
        "Tractor for Commercial Use": 4,
        "Trailer Attached To Goods Vehicle": 4,  # Trailer wheels
        "Trailer Attached to Other Vehicle": 2,
        "Trailer for Agriculture Purpose": 2,
        "Trailer For Commercial Use": 4,
        "Trailer to Carry Personnel Efforts": 2,
        "Tree Trimming Vehicle": 4,
        "Trl.Att.To Fire Tender/Road Water Sprinkler": 4,
        "Truck Mounted Vacum Cleaner Machine": 6,
        "Vehicle Fitted with Construction Equipment": 4,
        "X-Ray van": 4,
    }

    @classmethod
    def get_wheels_for_cov(cls, class_of_vehicle: Optional[str]) -> Optional[int]:
        """
        Get the number of wheels for a given class of vehicle.

        Args:
            class_of_vehicle: The class of vehicle string

        Returns:
            Number of wheels or None if not found/undefined
        """
        if not class_of_vehicle:
            return None
        return cls.COV_TO_WHEELS_MAPPING.get(class_of_vehicle)
