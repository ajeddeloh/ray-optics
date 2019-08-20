#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © 2019 Michael J. Hayford
"""

.. Created on Tue Aug  6 18:08:16 2019

.. codeauthor: Michael J. Hayford
"""
import math
from collections import namedtuple

from rayoptics.util import dict2d
from rayoptics.util.dict2d import dict2D


obj_img_set = ['object', 'image']
fld_ape_set = ['field', 'aperture']
fld_labels = ['height', 'angle']
ap_labels = ['pupil', 'NA', 'f/#']


def na2slp(na, n=1.0):
    """ convert numerical aperture to slope """
    return n*math.tan(math.asin(na/n))


def slp2na(slp, n=1.0):
    """ convert a ray slope to numerical aperture """
    return n*math.sin(math.atan(slp/n))


def ang2slp(ang):
    """ convert an angle in degrees to a slope """
    return math.tan(math.radians(ang))


def slp2ang(slp):
    """ convert a slope to an angle in degrees """
    return math.degrees(math.atan(slp))


def do_etendue_via_imager(conj_type, imager, etendue_inputs, etendue_grid,
                          n_0=1, n_k=1):
    li = dict2d.num_items_by_type(etendue_inputs, fld_ape_set, obj_img_set)
    if li['field'] == 1:
        row = dict2d.row(etendue_inputs, 'field')
        obj_img_key = 'object' if len(row['object']) else 'image'
        do_field_via_imager(conj_type, imager, etendue_inputs, obj_img_key,
                            etendue_grid, n_0=n_0, n_k=n_k)

    if li['aperture'] == 1:
        row = dict2d.row(etendue_inputs, 'aperture')
        obj_img_key = 'object' if len(row['object']) else 'image'
        do_aperture_via_imager(conj_type, imager, etendue_inputs, obj_img_key,
                               etendue_grid)

    imager_inputs = None
    if li['field'] == 2:
        obj_cell = etendue_inputs['field']['object']
        img_cell = etendue_inputs['field']['image']
        obj_grid = etendue_grid['field']['object']
        img_grid = etendue_grid['field']['image']
        obj_key = obj_cell.keys()
        img_key = img_cell.keys()
        if 'angle' in obj_key:
            obj_ang = obj_cell['angle']
            obj_slp = ang2slp(obj_ang)
            if 'height' in img_key:
                img_ht = img_cell['height']
                img_grid['height'] = img_ht
                efl = img_ht/obj_slp
                imager_inputs = 'f', efl
            else:
                return None
        elif 'height' in obj_key:
            obj_ht = obj_cell['height']
            if 'height' in img_key:
                img_ht = img_cell['height']
                img_grid['height'] = img_ht
                mag = img_ht/obj_ht
                imager_inputs = 'm', mag

    if li['aperture'] == 2:
        obj_cell = etendue_inputs['aperture']['object']
        img_cell = etendue_inputs['aperture']['image']
        obj_grid = etendue_grid['aperture']['object']
        img_grid = etendue_grid['aperture']['image']
        obj_key = obj_cell.keys()
        img_key = img_cell.keys()
        if 'pupil' in obj_key:
            epd = obj_cell['pupil']
            if 'f/#' in img_key:
                fno = img_cell['f/#']
                img_grid['f/#'] = fno
                efl = epd * fno
                imager_inputs = 'f', efl
            if 'NA' in img_key:
                na = img_cell['NA']
                img_grid['NA'] = na
                slpk = na2slp(na, n=n_k)
                efl = (epd/2.0)/slpk
                imager_inputs = 'f', efl
        else:
            if 'NA' in obj_key:
                nao = obj_cell['NA']
                obj_grid['NA'] = nao
                slp0 = na2slp(nao, n=n_0)
            elif 'f/#' in obj_key:
                fno = obj_cell['f/#']
                obj_grid['f/#'] = fno
                slp0 = -1/(2*fno)

            if 'NA' in img_key:
                na = img_cell['NA']
                img_grid['NA'] = na
                slpk = na2slp(na, n=n_k)
            elif 'f/#' in img_key:
                fno = img_cell['f/#']
                img_grid['f/#'] = fno
                slpk = -1/(2*fno)
            mag = slp0/slpk
            imager_inputs = 'f', efl
    return imager_inputs


def do_field_via_imager(conj_type, imager, etendue_inputs, obj_img_key,
                        etendue_grid, n_0=1, n_k=1):
    input_cell = etendue_inputs['field'][obj_img_key]
    input_grid_cell = etendue_grid['field'][obj_img_key]
    if obj_img_key is 'object':
        output_cell = etendue_grid['field']['image']
        if 'angle' in input_cell:
            efl = imager.f
            obj_ang = input_cell['angle']
            input_grid_cell['angle'] = obj_ang
            obj_slp = ang2slp(obj_ang)
            output_cell['height'] = efl*obj_slp
        elif 'height' in input_cell:
            m = imager.m
            obj_ht = input_cell['height']
            input_grid_cell['height'] = obj_ht
            output_cell['height'] = m*obj_ht

    elif obj_img_key is 'image':
        output_cell = etendue_grid['field']['object']
        if imager.m == 0:  # infinite conjugate
            efl = imager.f
            if 'height' in input_cell:
                img_ht = input_cell['height']
                input_grid_cell['height'] = img_ht
                obj_slp = img_ht/efl
                obj_ang = slp2ang(obj_slp)
                output_cell['angle'] = obj_ang
        else:  # finite conjugate
            m = imager.m
            if 'height' in input_cell:
                img_ht = input_cell['height']
                input_grid_cell['height'] = img_ht
                output_cell['height'] = m/img_ht


def do_aperture_via_imager(conj_type, imager, etendue_inputs, obj_img_key,
                           etendue_grid, n_0=1, n_k=1):
    input_cell = etendue_inputs['aperture'][obj_img_key]
    input_grid_cell = etendue_grid['aperture'][obj_img_key]
    if conj_type is 'infinite':
        efl = imager.f

        if obj_img_key is 'object':
            epd = input_cell['pupil']
            input_grid_cell['pupil'] = epd
            slpk = (epd/2.0)/efl
            na, fno = get_aperture_from_slope(slpk, n=n_k)
            output_cell = etendue_grid['aperture']['image']

            na, fno = get_aperture_from_slope(slpk, n=n_k)
            output_cell = etendue_grid['aperture']['image']
            output_cell['f/#'] = fno
            output_cell['NA'] = na

        elif obj_img_key is 'image':
            slpk = get_slope_from_aperture(input_cell, n=n_k)
            na, fno = get_aperture_from_slope(slpk, n=n_k)
            input_grid_cell['f/#'] = fno
            input_grid_cell['NA'] = na

            epd = 2*slpk*efl

            output_cell = etendue_grid['aperture']['object']
            output_cell['pupil'] = epd

    else:
        mag = imager.m

        if obj_img_key is 'object':
            slp0 = get_slope_from_aperture(input_cell, n=n_0)
            na, fno = get_aperture_from_slope(slp0, n=n_0)
            input_grid_cell['f/#'] = fno
            input_grid_cell['NA'] = na

            slpk = slp0/mag
            na, fno = get_aperture_from_slope(slpk, n=n_k)
            output_cell = etendue_grid['aperture']['image']

        elif obj_img_key is 'image':
            slpk = get_slope_from_aperture(input_cell, n=n_k)
            na, fno = get_aperture_from_slope(slpk, n=n_k)
            input_grid_cell['f/#'] = fno
            input_grid_cell['NA'] = na

            slp0 = mag*slpk
            na, fno = get_aperture_from_slope(slp0, n=n_0)
            output_cell = etendue_grid['aperture']['object']

        output_cell['f/#'] = fno
        output_cell['NA'] = na


def get_aperture_from_slope(slope, n=1):
    fno = -1/(2*slope)
    na = slp2na(slope, n=n)
    return na, fno


def get_slope_from_aperture(input_cell, n=1):
    if 'NA' in input_cell:
        na = input_cell['NA']
        slope = na2slp(na, n=n)
    elif 'f/#' in input_cell:
        fno = input_cell['f/#']
        slope = -1/(2*fno)
    else:
        slope = None
    return slope


def do_etendue_to_imager(inputs, grid, n_0=1.0, n_k=1.0):
    li = dict2d.num_items_by_type(inputs, fld_ape_set, obj_img_set)
    if li['field'] == 2:
        obj_cell = inputs['field']['object']
        img_cell = inputs['field']['image']
        obj_key = obj_cell.keys()
        img_key = img_cell.keys()
        if 'angle' in obj_key:
            obj_ang = obj_cell['angle']
            obj_slp = ang2slp(obj_ang)
            if 'height' in img_key:
                img_ht = img_cell['height']
                efl = img_ht/obj_slp
                imager_inputs = 'f', efl
            else:
                return None
        elif 'height' in obj_key:
            obj_ht = obj_cell['height']
            if 'height' in img_key:
                img_ht = img_cell['height']
                mag = img_ht/obj_ht
                imager_inputs = 'm', mag

    elif li['aperture'] == 2:
        obj_cell = inputs['aperture']['object']
        img_cell = inputs['aperture']['image']
        obj_key = obj_cell.keys()
        img_key = img_cell.keys()
        if 'pupil' in obj_key:
            epd = obj_cell['pupil']
            if 'f/#' in img_key:
                fno = img_cell['f/#']
                efl = epd * fno
                imager_inputs = 'f', efl
            if 'NA' in img_key:
                na = img_cell['NA']
                slpk = na2slp(na, n=n_k)
                efl = (epd/2.0)/slpk
                imager_inputs = 'f', efl
        else:
            if 'NA' in obj_key:
                nao = obj_cell['NA']
                slp0 = na2slp(nao, n=n_0)
            elif 'f/#' in obj_key:
                fno = obj_cell['f/#']
                slp0 = -1/(2*fno)

            if 'NA' in img_key:
                na = img_cell['NA']
                slpk = na2slp(na, n=n_k)
            elif 'f/#' in obj_key:
                fno = img_cell['f/#']
                slpk = -1/(2*fno)
            mag = slp0/slpk
            imager_inputs = 'f', efl
    return imager_inputs
