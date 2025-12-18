"""
MemoryService - 管理长期记忆 (LTM)
支持结构化存储、版本管理、压缩追溯
"""
import json
import shutil
from datetime import datetime, timezone, timedelta

# 中国时区 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))

def get_china_now() -> datetime:
    """获取中国时间"""
    return datetime.now(CHINA_TZ)
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class LTMData:
    """长期记忆数据结构"""
    summary_text: str
    last_summary_time: str
    summary_version: int
    source_window: Dict[str, Any]  # {start_msg_id, end_msg_id, start_time, end_time}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MemoryService:
    """记忆服务"""
    
    def __init__(self, memory_base_path: Optional[Path] = None):
        self.memory_base_path = memory_base_path or (
            Path(__file__).parent.parent.parent / "memory" / "本体"
        )
    
    def _get_user_dir(self, user_id: int) -> Path:
        """获取用户记忆目录"""
        user_dir = self.memory_base_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def _get_ltm_dir(self, user_id: int) -> Path:
        """获取LTM目录"""
        ltm_dir = self._get_user_dir(user_id) / "ltm"
        ltm_dir.mkdir(parents=True, exist_ok=True)
        return ltm_dir
    
    def _get_ltm_file(self, user_id: int) -> Path:
        """获取当前LTM文件路径"""
        return self._get_ltm_dir(user_id) / "ltm.json"
    
    def _get_legacy_ltm_file(self, user_id: int) -> Path:
        """获取旧版long_term.txt路径"""
        return self._get_user_dir(user_id) / "memory" / "long_term.txt"
    
    def read_ltm(self, user_id: int) -> Optional[LTMData]:
        """读取用户的长期记忆"""
        ltm_file = self._get_ltm_file(user_id)
        
        if ltm_file.exists():
            try:
                with open(ltm_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return LTMData(
                    summary_text=data.get("summary_text", ""),
                    last_summary_time=data.get("last_summary_time", ""),
                    summary_version=data.get("summary_version", 1),
                    source_window=data.get("source_window", {}),
                )
            except Exception:
                pass
        
        # 尝试从旧版long_term.txt迁移
        legacy_file = self._get_legacy_ltm_file(user_id)
        if legacy_file.exists():
            try:
                text = legacy_file.read_text(encoding="utf-8").strip()
                if text:
                    return LTMData(
                        summary_text=text,
                        last_summary_time=get_china_now().isoformat(),
                        summary_version=0,  # 迁移版本标记为0
                        source_window={},
                    )
            except Exception:
                pass
        
        return None
    
    def read_ltm_text(self, user_id: int) -> str:
        """读取LTM文本内容（兼容旧接口）"""
        ltm = self.read_ltm(user_id)
        if ltm:
            return ltm.summary_text
        return ""
    
    def write_ltm(
        self,
        user_id: int,
        summary_text: str,
        source_window: Optional[Dict[str, Any]] = None,
    ) -> LTMData:
        """
        写入长期记忆
        
        会自动：
        1. 递增版本号
        2. 备份旧版本
        3. 同时更新legacy long_term.txt
        """
        ltm_dir = self._get_ltm_dir(user_id)
        ltm_file = self._get_ltm_file(user_id)
        
        # 读取现有版本
        current_version = 0
        if ltm_file.exists():
            try:
                with open(ltm_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                current_version = data.get("summary_version", 0)
                
                # 备份旧版本
                backup_file = ltm_dir / f"ltm_v{current_version}.json"
                shutil.copy2(ltm_file, backup_file)
            except Exception:
                pass
        
        # 创建新的LTM数据
        new_version = current_version + 1
        ltm_data = LTMData(
            summary_text=summary_text,
            last_summary_time=get_china_now().isoformat(),
            summary_version=new_version,
            source_window=source_window or {},
        )
        
        # 写入新版本
        with open(ltm_file, "w", encoding="utf-8") as f:
            json.dump(ltm_data.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 同时更新legacy文件（兼容）
        legacy_file = self._get_legacy_ltm_file(user_id)
        legacy_file.parent.mkdir(parents=True, exist_ok=True)
        legacy_file.write_text(summary_text, encoding="utf-8")
        
        return ltm_data
    
    def get_ltm_versions(self, user_id: int) -> List[Dict[str, Any]]:
        """获取LTM版本历史"""
        ltm_dir = self._get_ltm_dir(user_id)
        if not ltm_dir.exists():
            return []
        
        versions = []
        for f in sorted(ltm_dir.glob("ltm_v*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                versions.append({
                    "file": f.name,
                    "version": data.get("summary_version"),
                    "time": data.get("last_summary_time"),
                })
            except Exception:
                pass
        
        # 添加当前版本
        ltm_file = self._get_ltm_file(user_id)
        if ltm_file.exists():
            try:
                with open(ltm_file, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                versions.append({
                    "file": "ltm.json",
                    "version": data.get("summary_version"),
                    "time": data.get("last_summary_time"),
                    "current": True,
                })
            except Exception:
                pass
        
        return sorted(versions, key=lambda x: x.get("version", 0))
    
    def rollback_ltm(self, user_id: int, version: int) -> bool:
        """回滚到指定版本"""
        ltm_dir = self._get_ltm_dir(user_id)
        backup_file = ltm_dir / f"ltm_v{version}.json"
        
        if not backup_file.exists():
            return False
        
        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 先备份当前版本
            ltm_file = self._get_ltm_file(user_id)
            if ltm_file.exists():
                current_data = json.load(open(ltm_file, "r", encoding="utf-8"))
                current_version = current_data.get("summary_version", 0)
                shutil.copy2(ltm_file, ltm_dir / f"ltm_v{current_version}.json")
            
            # 恢复指定版本（版本号+1）
            new_version = data.get("summary_version", version) + 1
            data["summary_version"] = new_version
            data["last_summary_time"] = get_china_now().isoformat()
            
            with open(ltm_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 更新legacy
            legacy_file = self._get_legacy_ltm_file(user_id)
            legacy_file.write_text(data.get("summary_text", ""), encoding="utf-8")
            
            return True
        except Exception:
            return False


# 单例
_memory_service: Optional[MemoryService] = None

def get_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
