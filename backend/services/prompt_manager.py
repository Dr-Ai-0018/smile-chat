"""
PromptManager - 管理三套提示词（情感/事实/无表露）
按 condition 加载对应的系统提示词
"""
from pathlib import Path
from typing import Optional

class PromptManager:
    """提示词管理器"""
    
    CONDITION_FILES = {
        "emotional": "情感表露.txt",
        "factual": "事实表露.txt",
        "none": "无表露.txt",
    }
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = prompts_dir or (Path(__file__).parent.parent / "prompts")
        self._cache: dict[str, str] = {}

    def get_prompt_filename(self, condition: str) -> str:
        filename = self.CONDITION_FILES.get(condition)
        if filename:
            return filename
        return self.CONDITION_FILES["emotional"]

    def get_prompt_path(self, condition: str) -> Path:
        return self.prompts_dir / self.get_prompt_filename(condition)

    def get_example_prompt_path(self, condition: str) -> Path:
        filename = self.get_prompt_filename(condition)
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        return self.prompts_dir / f"{stem}_示例{suffix}"

    def get_active_prompt_path(self, condition: str) -> Optional[Path]:
        prompt_path = self.get_prompt_path(condition)
        if prompt_path.exists() and prompt_path.is_file():
            return prompt_path

        example = self.get_example_prompt_path(condition)
        if example.exists() and example.is_file():
            return example

        return None

    def get_prompt_source(self, condition: str) -> str:
        active = self.get_active_prompt_path(condition)
        if active is None:
            return "fallback"
        if active.resolve() == self.get_prompt_path(condition).resolve():
            return "prompt"
        return "example"
    
    def get_system_prompt(self, condition: str = "emotional") -> str:
        """
        根据实验条件加载系统提示词
        
        Args:
            condition: 'emotional' | 'factual' | 'none'
        
        Returns:
            系统提示词文本
        """
        if condition in self._cache:
            return self._cache[condition]
        
        prompt_file = self.get_active_prompt_path(condition)
        if prompt_file is None:
            return self._get_fallback_prompt()
        
        try:
            content = prompt_file.read_text(encoding="utf-8").strip()
            if not content:
                return self._get_fallback_prompt()
            self._cache[condition] = content
            return content
        except Exception:
            return self._get_fallback_prompt()
    
    def _get_fallback_prompt(self) -> str:
        """默认提示词（当文件不存在时）"""
        return """你是启明，一个友好的AI聊天伙伴。
你的目标是和用户建立自然、舒服的对话关系。
请用简短、温暖的语气回复，每条回复控制在20个汉字左右。
"""
    
    def reload(self, condition: Optional[str] = None):
        """重新加载提示词（清除缓存）"""
        if condition:
            self._cache.pop(condition, None)
        else:
            self._cache.clear()


# 单例
_prompt_manager: Optional[PromptManager] = None

def get_prompt_manager() -> PromptManager:
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
