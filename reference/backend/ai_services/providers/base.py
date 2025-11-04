from abc import ABC, abstractmethod
from typing import Any, Dict

class ITranscriber(ABC):
    """
    Interface (Contract) for transcription capability.
    Defines the standard method that all transcription providers must implement.
    "I" stands for Interface, a common convention.
    """

    @abstractmethod
    async def transcribe(self, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronously transcribes an audio file and returns the result.

        :param file_path: Path to the audio file.
        :param config: A dictionary with configuration options,
                       e.g., {"language": "en", "enable_alignment": True}.
        :return: A dictionary containing the transcription result.
        """
        pass

# In the future, other capability interfaces can be added here.
# For example:
#
# class IDiarizer(ABC):
#     """Interface for speaker diarization capability."""
#     @abstractmethod
#     def diarize(self, file_path: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
#         pass

