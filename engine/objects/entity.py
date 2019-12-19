
from __future__ import annotations

from structs.vector import Vector
from engine.objects.base import ScriptableObject
from engine.mixins.nameable import Nameable
from engine.objects.component import Component
import engine
import engine.utils

from typing import TYPE_CHECKING, Type, List, Callable

if TYPE_CHECKING:
    from engine.scene import Scene


class Entity(ScriptableObject, Nameable):
    """
    An Entity is a game object that is composed of multiple components.
    """
    def __init__(self, pos: tuple, scene: Scene, name: str = None,
                 *args, **kwargs):
        """
        Create an Entity.

        Args:
            pos (tuple, optional): the position to spawn this entity
        """
        super().__init__(pos=pos, name=name, *args, **kwargs)

        # the Scene that spawned this entity
        self.scene: Scene = scene

        # the root Component of this entity
        self.root_component: Component = Component(pos=pos, name='Root')

    def create_component(self, cmp_class: Type[engine.T],
                         pos: tuple = (0, 0), *args, **kwargs) -> engine.T:
        kwargs['scene'] = self.scene  # manually add scene
        return engine.create_component(cmp_class, pos,
                                       parent=self.root_component,
                                       *args, **kwargs)

    # --------------------------------------------------------------------------
    # Events (to be overridden by subclasses)
    # --------------------------------------------------------------------------

    @property  # type: ignore
    def position(self) -> Vector:
        return self.root_component.position

    @position.setter  # type: ignore
    def position(self, pos: tuple):
        self.root_component.position = pos  # type: ignore

    def on_key_press(self, symbol, modifier):
        """Called every time a key is pressed."""
        pass

    def on_key_release(self, symbol, modifier):
        """Called every time a key was released."""
        pass
