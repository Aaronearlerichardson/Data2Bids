# Raw2Bids

Raw2Bids reorganises raw files from any extension into the [Brain Imaging Data Structure](http://bids.neuroimaging.io/).
The user specify how the files should be read into a directory. Then the tool scan all the files and move them into the right directories.

###### Input

A directory containing some files in any extension, with names containing at minimum the information of modality and patient number.
A `.JSON` configuration file explaining how the filenames should be read.

###### Output

A directory as specified by the BIDS standard.

###### Example

A directory `MyDataset` with the following files :
```
MyDataset/
|
└── adhd_41278_FU12_T1_001.nii
|
└── adhd_41278_FU24_T1_001.nii
|
└── adhd_41578_BL00_RSFMRI_001.nii
|
└── adhd_41578_BL00_RSFMRI_002.nii
```

Will be transformed as :

```
MyDataset/
|
└── sub-41278/
|   |
|   └── anat/
|       |
|       └── adhd_41278_FU12_T1_001.nii
|       |
|       └── adhd_41278_FU24_T1_001.nii
└── sub-41578/
    |
    └── func/
        |
        └── adhd_41578_BL00_RSFMRI_001.nii
        |
        └── adhd_41578_BL00_RSFMRI_002.nii
```

## Install

###### with pip

###### with singularity

## Introduction

## Usage

## bids-validator

You can run the [https://github.com/bids-standard/bids-validator](BIDS-validator) to check your directory.