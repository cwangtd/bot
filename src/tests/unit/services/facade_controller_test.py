from app.services.facade_controller import FacadeController
from app.storage.storage_utils import CloudStorage
from tests import LOCAL_DEV_ENV


def test_session_id():
    fc1 = FacadeController(
        storage=CloudStorage.GCS,
        bucket='provenance-aigc-storage',
        path='provenance.local.dev/tests/elsa.jpg',
        env=LOCAL_DEV_ENV
    )
    fc2 = FacadeController(
        storage=CloudStorage.S3,
        bucket='provenance-aigc-storage',
        path='provenance.local.dev/tests/elsa.jpg',
        env=LOCAL_DEV_ENV
    )

    assert fc1.shooter.response_id != fc2.shooter.response_id
