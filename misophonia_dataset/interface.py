from abc import ABC
from enum import Enum
from pathlib import Path

class Split(Enum):
    test: str = 


class SourceData(ABC):
    def get_metadata() -> pd.DataFrame:
        # columns: 
        # id, license_url, licence_aatribution, ..., 
        # misophnia_labels
        # audioset_labels
        # split
        # audio_path
        pass


class FreeSound(ABC):
    pass

class ESC50(SourceData):
    def __init__(self,
               metadata: str,
               label_column_name: Path, #label column name in metadata
               fname_column_name: Path, # fname column name in metadata
               mapping: Path):
        pass

    def download_sounds()

class FSDK50(Dataset):
    def __init__(self,
               metadata: str,
               label_column_name: Path, #label column name in metadata
               fname_column_name: Path, # fname column name in metadata
               mapping: Path):
        pass

class FOAMS(Dataset):
    def __init__(self,
               metadata: str,
               label_column_name: Path, #label column name in metadata
               fname_column_name: Path, # fname column name in metadata
            ):
        pass    
        


class MisophoniaData:
    def __init__(self, source_data: list[SourceData]) -> None:
        self._source_data = source_data
        pass

    def generate(self):
        pass

class MisophoniaItem:
    component_sounds =
    duration
    amplitude

    pass

def generate_misophonia_data(source_data: list[SourceData], split: Split) -> Generator[MisophoniaItem]:
    combined_metadata = pd.DataFrame

    while True:
        yield MisophoniaItem()

