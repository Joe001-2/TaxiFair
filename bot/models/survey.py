from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any

@dataclass
class Question:
    id: str
    text: str
    label: str
    type: str  # 'text', 'contact', 'choice', 'time'
    options: Any = None
    validator: Optional[Callable[[str], tuple[bool, str]]] = None
    keyboard_type: str = "none"  # "reply", "inline", "none"

@dataclass
class Survey:
    id: str
    title: str
    questions: List[Question] = field(default_factory=list)
