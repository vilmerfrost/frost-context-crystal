import zlib
import base64
from typing import Optional

class ContentCompressor:
    def __init__(self):
        self.compression_level = 6
    
    def compress_content(self, content: str) -> Optional[str]:
        try:
            compressed_data = zlib.compress(content.encode('utf-8'), self.compression_level)
            return base64.b64encode(compressed_data).decode('utf-8')
        except Exception as e:
            print(f"Compression error: {e}")
            return None
    
    def decompress_content(self, compressed_content: str) -> Optional[str]:
        try:
            compressed_data = base64.b64decode(compressed_content)
            return zlib.decompress(compressed_data).decode('utf-8')
        except Exception as e:
            print(f"Decompression error: {e}")
            return None