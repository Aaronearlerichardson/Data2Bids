#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 21 11:55:12 2018

@author: ltetrel
"""
import os
import re
import shutil
import json
import subprocess
import gzip
#import sys
#sys.path.insert(0, os.getcwd())
import numpy as np
import nibabel as nib
import data2bids.utils as utils

class Data2Bids():

    def __init__(self, input_dir=None, config=None, output_dir=None, multi_echo=None):
        self._input_dir = None
        self._config_path = None
        self._config = None
        self._bids_dir = None
        self._bids_version = "1.1.1"
        self._dataset_name = None

        self.set_data_dir(input_dir)
        self.set_config_path(config)
        self.set_bids_dir(output_dir)
        self.set_multi_echo(multi_echo)

    def set_multi_echo(self,multi_echo):
        if multi_echo is None:
            self.is_multi_echo = False
        else:
            self.is_multi_echo = True
            if not multi_echo:
                self._multi_echo = 0
            else:
                self._multi_echo = multi_echo

        self._multi_echo = multi_echo

    def get_data_dir(self):
        return self._data_dir

    def set_data_dir(self, data_dir):
        if data_dir is None:
            self._data_dir = os.getcwd()
        else:
            self._data_dir = data_dir

        self._dataset_name = os.path.basename(self._data_dir)

    def get_config(self):
        return self._config

    def get_config_path(self):
        return self._config_path

    def _set_config(self):
        with open(self._config_path, 'r') as fst:
            self._config = json.load(fst)

    def set_config(self, config):
        self._config = config

    def set_config_path(self, config_path):
        if config_path is None:
            # Checking if a config.json is present
            if os.path.isfile(os.path.join(os.getcwd(), "config.json")):
                self._config_path = os.path.join(os.getcwd(), "config.json")
            # Otherwise taking the default config
            else:
                self._config_path = os.path.join(os.path.dirname(__file__), "config.json")
        else:
            self._config_path = config_path

        self._set_config()

    def get_bids_dir(self):
        return self._bids_dir

    def set_bids_dir(self, bids_dir):
        if bids_dir is None:
            # Creating a new directory for BIDS
            try:
                self._bids_dir = os.path.join(self._data_dir, self._dataset_name + "_BIDS")
            except TypeError:
                print("Error: Please provide input data directory if no BIDS directory...")
        else:
            self._bids_dir = bids_dir

    def get_bids_version(self):
        return self._bids_version

    def match_regexp(self, config_regexp, filename, subtype=False):
        delimiter_left = config_regexp["left"]
        delimiter_right = config_regexp["right"]
        match_found = False

        if subtype:
            for to_match in config_regexp["content"]:
                if re.match(".*?"
                            + delimiter_left
                            + '(' + to_match[1] + ')'
                            + delimiter_right
                            + ".*?", filename):
                    match = to_match[0]
                    match_found = True
        else:
            for to_match in config_regexp["content"]:
                if re.match(".*?"
                            + delimiter_left
                            + '(' + to_match + ')'
                            + delimiter_right
                            + ".*?", filename):
                    match = re.match(".*?"
                                     + delimiter_left
                                     + '(' + to_match + ')'
                                     + delimiter_right
                                     + ".*?", filename).group(1)
                    match_found = True

        assert match_found
        return match

    def bids_validator(self):
        assert self._bids_dir is not None, "Cannot launch bids-validator without specifying bids directory !"
        try:
            subprocess.check_call(['bids-validator', self._bids_dir])
        except FileNotFoundError:
            print("bids-validator does not appear to be installed")

    def maketsv(self,tsv_dir):
        for folder in tsv_dir :
            for file in folder :
                return()

    def run(self):

        # First we check that every parameters are configured
        if (self._data_dir is not None
                and self._config_path is not None
                and self._config is not None
                and self._bids_dir is not None):

            print("---- data2bids starting ----")
            print(self._data_dir)
            print("\n BIDS version:")
            print(self._bids_version)
            print("\n Config from file :")
            print(self._config_path)
            print("\n Ouptut BIDS directory:")
            print(self._bids_dir)
            print("\n")

            # Create the output BIDS directory
            if os.path.exists(self._bids_dir):
                shutil.rmtree(self._bids_dir)
            os.makedirs(self._bids_dir)

            # What is the base format to convert to
            curr_ext = self._config["dataFormat"]
            compress = self._config["compress"]

            # delay time in TR unit (if delay_time = 1, delay_time = repetition_time)
            repetition_time = self._config["repetitionTimeInSec"]
            delaytime = self._config["delayTimeInSec"]

            #dataset_description.json must be included in the folder root foolowing BIDS specs
            with open(self._bids_dir + "/dataset_description.json", 'w') as fst:
                data = {'Name': self._dataset_name,
                        'BIDSVersion': self._bids_version}
                json.dump(data, fst, ensure_ascii=False)

            # now we can scan all files and rearrange them
            for root, tsv_dir, files in os.walk(self._data_dir):
                i = 0
                sidecar_file_path = ""
                for file in files:
                    
                    src_file_path = os.path.join(root, file)
                    dst_file_path = self._bids_dir

                    part_match = None
                    sess_match = None
                    data_type_match = None
                    run_match = None
                    new_name = None
                    
                    if re.match(".*?" + ".json", file):
                        sidecar_file_path = src_file_path
                        continue
                    elif re.match(".*?" + "README.txt", file): 
                        shutil.copy(src_file_path, dst_file_path +"README.txt")
                        continue
                    elif re.match(".*?" + ".1D", file): 
                        continue
                    # if the file doesn't match the extension, we skip it
                    elif not any(re.match(".*?" + ext, file) for ext in curr_ext):
                        print("Warning : Skipping %s" %src_file_path)
                        continue
                    #print("trying %s" %src_file_path)
                    # Matching the participant label
                    try:
                        part_match = self.match_regexp(self._config["partLabel"], file)
                        dst_file_path = dst_file_path + "/sub-" + part_match
                        new_name = "/sub-" + part_match
                    except AssertionError:
                        print("No participant found for %s" %src_file_path)
                        continue

                    # Matching the session
                    try:
                        sess_match = self.match_regexp(self._config["sessLabel"], file)
                        dst_file_path = dst_file_path + "/ses-" + sess_match
                        new_name = new_name + "_ses-" + sess_match
                    except AssertionError:
                        print("No session found for %s" %src_file_path)
                        continue

                    # Matching the anat/fmri data type and task
                    try:
                        data_type_match = self.match_regexp(self._config["anat"]
                                                            , file
                                                            , subtype=True)
                        dst_file_path = dst_file_path + "/anat"

                        try:
                            acq_label_match = self.match_regexp(self._config["anat.acq"]
                                                                    , file
                                                                    , subtype=True)
                            new_name = new_name + "_acq-" + acq_label_match
                        except AssertionError:
                            print("no optional labels for %s" %src_file_path)
                            #    continue
                    except AssertionError:
                        # If no anatomical, trying functionnal
                        try:
                            data_type_match = self.match_regexp(self._config["func"]
                                                                , file
                                                                , subtype=True)
                            dst_file_path = dst_file_path + "/func"
                            # Now trying to match the task
                            try:
                                task_label_match = self.match_regexp(self._config["func.task"]
                                                                     , file
                                                                     , subtype=True)
                                new_name = new_name + "_task-" + task_label_match
                            except AssertionError:
                                print("No task found for %s" %src_file_path)
                                continue
                        except AssertionError:
                            print("No anat nor func data type found for %s" %src_file_path)
                            continue

                    # Matching the run number
                    try:
                        run_match = self.match_regexp(self._config["runIndex"], file)
                        new_name = new_name + "_run-" + run_match
                    except AssertionError:
                        print("No run found for %s" %src_file_path)

                    if self.is_multi_echo :
                        if int(run_match) in self._multi_echo:
                            try:
                                echo_match = self.match_regexp(self._config["echo"], file)
                                new_name = new_name + "_echo-" + echo_match
                            except AssertionError:
                                print("No echo found for %s" %src_file_path)
                                continue
                        

                    # Adding the modality to the new filename
                    new_name = new_name + "_" + data_type_match

                    # Creating the directory where to store the new file
                    if not os.path.exists(dst_file_path):
                        os.makedirs(dst_file_path)

                    # finally, if the file is not nifti, we convert it using nibabel
                    if not ".nii" in curr_ext or not ".nii.gz" in curr_ext:
                        # loading the original image
                        nib_img = nib.load(src_file_path)
                        nib_affine = np.array(nib_img.affine)
                        nib_data = np.array(nib_img.dataobj)

                        # create the nifti1 image
                        # if minc format, invert the data and change the affine transformation
                        # there is also an issue on minc headers, TO CHECK...
                        if curr_ext == ".mnc":
                            if len(nib_img.shape) > 3:
                                nib_affine[0:3, 0:3] = nib_affine[0:3, 0:3] \
                                    @ utils.rot_z(np.pi/2) \
                                    @ utils.rot_y(np.pi) \
                                    @ utils.rot_x(np.pi/2)
                                nib_data = nib_data.T
                                nib_data = np.swapaxes(nib_data, 0, 1)

                                nifti_img = nib.Nifti1Image(nib_data, nib_affine, nib_img.header)
                                nifti_img.header.set_xyzt_units(xyz="mm", t="sec")
                                zooms = np.array(nifti_img.header.get_zooms())
                                zooms[3] = repetition_time
                                nifti_img.header.set_zooms(zooms)
                            elif len(nib_img.shape) == 3:
                                nifti_img = nib.Nifti1Image(nib_data, nib_affine, nib_img.header)
                                nifti_img.header.set_xyzt_units(xyz="mm")
                        else:
                            nifti_img = nib.Nifti1Image(nib_data, nib_affine, nib_img.header)

                        #saving the image
                        nib.save(nifti_img, dst_file_path + new_name + ".nii.gz")

                    # if it is already a nifti file, no need to convert it so we just copy rename
                    elif ".nii.gz" in file:
                        shutil.copy(src_file_path, dst_file_path + new_name + ".nii.gz")
                    else:
                        shutil.copy(src_file_path, dst_file_path + new_name + ".nii")
                        #compression just if .nii files
                        if compress is True:
                            print("zipping " + file)
                            with open(dst_file_path + new_name + ".nii", 'rb') as f_in:
                                with gzip.open(dst_file_path + new_name + ".nii.gz", 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            os.remove(dst_file_path + new_name + ".nii")

                    # move the sidecar from input to output
                    if sidecar_file_path.replace(".json","") == src_file_path.split(".ni")[0]:
                        shutil.copy(sidecar_file_path, dst_file_path + new_name + ".json")


                    # finally, if it is a bold experiment, we need to add the JSON file
                    if data_type_match == "bold":
                        ### https://github.com/nipy/nibabel/issues/712, that is why we take the
                        ### scanner parameters from the config.json
                        #nib_img = nib.load(src_file_path)
                        #TR = nib_img.header.get_zooms()[3]
                        try:
                            with open(dst_file_path + new_name + ".json", 'w') as fst:
                                data = {'RepetitionTime': float(repetition_time),
                                        'TaskName': task_label_match,
                                        'DelayTime' : delaytime.split()[i]}
                                if i < (len(data['DelayTime']-1)):
                                    i += 1 
                                json.dump(data, fst, ensure_ascii=False)
                        except FileNotFoundError:
                            print("Cannot write %s" %(dst_file_path + new_name + ".nii.gz"))
                            continue
                #'''
                
                        

            # Output
            utils.tree(self._bids_dir)

            # Finally, we check with bids_validator if everything went alright (This wont work)
            #self.bids_validator()

        else:
            print("Warning: No parameters are defined !")
