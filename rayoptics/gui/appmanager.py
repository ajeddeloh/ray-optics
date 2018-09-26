#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © 2018 Michael J. Hayford
""" Lightweight manager class to connect a model+actions to windows

Created on Fri Aug 17 11:35:01 2018

@author: Michael J. Hayford
"""
import logging

from collections import namedtuple

ModelInfo = namedtuple('ModelInfo', ['model', 'fct', 'args', 'kwargs'])
# model is required; fct, args and kwargs are optional
ModelInfo.__new__.__defaults__ = (None, (), {})


class AppManager:
    """ Lightweight model/view manager class

    Lightweight manager class to manage connections between a model and
    a ui view.

    The main function of AppManager is refresh_gui(). This is called after
    a user input to the gui to update the model and call a refresh function
    for each ui view of that model.

    Attributes:
        model: the model of the currently active/frontmost ui view
            model is expected to respond to:
            update_model()
            name()
        view_dict: keys are ui views, values are ModelInfo tuples
            view is expected to implement:
                windowTitle() - only for debug logging
    """

    def __init__(self, model):
        self.model = model
        self.view_dict = {}

    def add_view(self, view, model_info):
        """ Add a new view and model tuple into dictionary

        Args:
            view: the ui view, used as a key
            model_info: instance of the ModelInfo tuple

        Returns:
            returns the input view
        """
        self.view_dict[view] = model_info
        return view

    def delete_view(self, view):
        """ removes view from the view dictionary

        Args:
            view: view being closed by user
        """
        del self.view_dict[view]

    def close_model(self, view_close_fct=None):
        """ close all ui views associated with the active model

        Args:
            view_close_fct: optional fct called on each closing view, with
                the view as an argument. This function, if used, should call
                delete_view itself.
        """
        cur_model = self.model
        view_items = list(self.view_dict.items())
        for view, mi in view_items:
            if mi.model == cur_model:
                if view_close_fct is None:
                    self.delete_view(view)
                else:
                    view_close_fct(view)

    def refresh_gui(self):
        """ update the active model and refresh it's dependent  ui views """
        self.model.update_model()
        for mi in self.view_dict.values():
            if mi.model == self.model:
                mi.fct(*mi.args, **mi.kwargs)

    def on_view_activated(self, view):
        """ Makes the model associated with input view the active model

        Args:
            view: view becoming the active view
        """
        if view is not None:
            try:
                mi = self.view_dict[view]
            except KeyError:
                logging.debug('view "%s" not in view_dict',
                              view.windowTitle())
            else:
                model = mi.model
                logging.debug("on_view_activated: %s, %s" %
                              (model.name(), view.windowTitle()))
                if model and model != self.model:
                    self.model = model
                    logging.debug("switch model to", model.name())
