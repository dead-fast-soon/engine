
"""Contains the base Component class."""

from __future__ import annotations

import inspect
from typing import (List, Optional, Union,
                    Type, TypeVar, Callable, TYPE_CHECKING)

from engine.objects.base import BaseObject
from structs.vector import Vector

if TYPE_CHECKING:
    from engine.game.scene import Scene


class Component(BaseObject):
    """
    Component is the base class for an object that defines behavior of
    an Entity.

    Components can also have child Components.
    """
    def __init__(self, pos: tuple = (0, 0), parent: Component = None):
        """
        Initializes a Component.

        Args:
            pos (tuple, optional): the position of this component
            parent (Component, optional): [description]. Defaults to None.
            view (Camera, optional): [description]. Defaults to None.

        """
        super().__init__(pos=pos)

        self._parent: Optional[Component] = parent
        self.children: List[Component] = []

    def add_component(self, *components: Component):
        """
        Add a child component to this component.

        Args:
            components (Component): the components to add

        """
        self.children.append(*components)

    def remove_component(self, *components: Component):
        """
        Remove a child component from this component.

        Args:
            components (Component): the components to remove
        """
        self.children.remove(*components)

    def render(self, delta: float):
        """
        Render this Component.

        Args:
            delta (float): the time difference from the last frame
        """
        for child in self.children:
            if isinstance(child, RenderedComponent): child.render(delta)

    def update(self, delta: float):
        """
        Update this Component.

        Args:
            delta (float): the time difference from the last tick
        """
        self.on_update(delta)
        for child in self.children:
            child.update(delta)

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def parent(self) -> Optional[Component]:
        """
        Get the parent Component of this Component.

        Returns:
            Component: the parent Component or None
        """
        return self._parent

    @parent.setter
    def parent(self, parent: Component):
        """
        Set the parent Component of this Component.

        Args:
            parent (Component): the new parent Component
        """
        if parent is not self._parent:  # run only if the parents are different
            if self._parent is not None and self in self._parent.children:
                parent.children.remove(self)  # remove self from old parent
            self._parent = parent
            if self not in parent.children:
                parent.children.append(self)  # add self to new parent

    @BaseObject.position.setter  # type: ignore
    def position(self, position: tuple):
        """
        Overrides `BaseObject.position` setter method

        Args:
            position (tuple): the new position of this component
        """

        a: Vector = self.position
        b: Vector = Vector(position)

        self._pos = b
        for child in self.children:
            child.position += (b.x - a.x, b.y - a.y)

        self.on_position_change()

    @property
    def local_position(self) -> Vector:
        """
        Get or set the position of this component with respect to the parent.

        If this component is the top-most in hierarchy (the parent), the
        position retrieved will be with respect to world-space.
        Otherwise, it will be with respect to the parent of this component
        (local).
        """
        if self.parent is None:
            return self.position
        else:
            a = self.position
            b = self.root.position
            return Vector(a.x - b.x, a.y - b.y)

    @property
    def root(self) -> Component:
        """
        Retrieve the top-most parent in the component heirarchy.
        """
        if self.parent is None:
            return self
        else:
            return self.parent.root

    # -------------------------------------------------------------------------
    # Events (to be overridden by subclasses)
    # -------------------------------------------------------------------------

    def on_update(self, delta: float):
        """Update this component on every tick."""
        pass

    def on_destroy(self):
        """
        Called when this Component needs to be deleted.
        """
        pass


class RenderedComponent(Component):
    """
    A RenderedComponent is a Component that is rendered
    using a render call.
    """

    def __init__(self, pos: tuple = (0, 0), parent: Component = None):
        """
        Create a RenderedComponent.

        Args:
            pos (tuple, optional): [description]. Defaults to (0, 0).
            parent (Component, optional): [description]. Defaults to None.
        """
        super().__init__(pos=pos, parent=parent)

    def render(self, delta: float):
        """
        Render this Component.

        Args:
            delta (float): the time difference from the last frame
        """
        self.on_render(delta)
        for child in self.children:
            if isinstance(child, RenderedComponent): child.render(delta)

    def on_render(self, delta: float):
        """Render this component on every frame."""
        pass

    @staticmethod
    def spawnable(old_init: Callable) -> Callable:
        """
        [summary]

        Args:
            old_init (typing.Callable): [description]

        Returns:
            typing.Callable: [description]
        """
        def wrapped_init(self, *args, pos: tuple, parent: Component, **kwargs):

            RenderedComponent.__init__(self, pos=pos, parent=parent)
            old_init(self, *args, **kwargs)

        return wrapped_init


class BatchComponent(Component):
    """
    A BatchComponent is a Component that is rendered using
    a batched render call from a Scene.
    """

    def __init__(self, scene: Scene,
                 pos: tuple = (0, 0), parent: Component = None):
        """
        Create a BatchComponent.

        Args:
            scene (Scene): the scene that renders this component
            pos (tuple, optional): the position of this component
            parent (Component, optional): the parent of this component
        """
        super().__init__(pos=pos, parent=parent)

        # the scene to use to render this component
        self.scene: Scene = scene

        # should this update every tick or every frame
        self.is_tickrate_uncapped = False

    def spawn_component(self, comp_cls, pos: Union[tuple, Vector],
                        *args, **kwargs):
        """
        Instantiate a new BatchComponent and add it to this one.
        """
        component = self.scene.spawn_component(comp_cls, pos, parent=self,
                                               *args, **kwargs)
        self.add_component(component)
        return component

    @staticmethod
    def spawnable(old_init: Callable) -> Callable:
        """
        Implicitly adds parameters needed to call
        `BatchComponent.__init__()`
        and implicitly calls `super().__init__()`.

        When using this decorator, it is recommended to create instances
        of this component using `Scene.spawn_component()`.

            class ExampleComponent(BatchComponent):
                @spawnable
                def __init__(self):
                    pass

            game = Game()
            scene = game.newScene()

            scene.spawn_component(ExampleComponent)
        """

        def wrapped_init(self, *args, pos: tuple, scene: Scene,
                         parent: Component, **kwargs):

            BatchComponent.__init__(self, scene=scene, pos=pos, parent=parent)
            old_init(self, *args, **kwargs)

        return wrapped_init