from enum import Enum


class WorkerTypes(str, Enum):
    EXAMPLE_WORKER = "example_worker"
    ID_GENERATION_REQUEST_WORKER = "id_generation_request_worker"
    ID_GENERATION_UPDATE_WORKER = "id_generation_update_worker"
    VEHICLE_OWNERSHIP_REGISTRY_WORKER = "vehicle_ownership_registry_worker"
    VEHICLE_OWNERSHIP_REGISTRY_BATCHING_WORKER = (
        "vehicle_ownership_registry_batching_worker"
    )
