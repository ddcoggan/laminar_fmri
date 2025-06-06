# laminar_fmri
Preprocessing pipeline for high-res fMRI at the 7T Phillips Achieva scanner in the Human Imaging department of the Vanderbilt Institute of Imaging Science.

This pipeline involves NORDIC preprocessing, based on the following paper: https://www.nature.com/articles/s41467-021-25431-8, and requires their MATLAB package. In this implementation, their package is called by python using the MATLAB engine. In practice, I have found that data quality (measured primarily based on tSNR in resting-state scans) is dependent on whether the magnitude and / or phase components are obtained directly from the scanner or  calculated from the real/imaginary components output by the scanner. The best configuration I found is to use the magnitude component from the scanner, and to calculate the phase component from the real and imaginary components.

Scanning procedure:
-	Run fieldmap and anatomical scans as normal.
-	Make sure each functional scan has 1 extra dynamic than the stimulus procedure, and saves out the Magnitude, Real, and Imaginary components.
-	Before the first functional scan, go to “Scan Control Parameters” and look for “Dyn. Noise Scan”. It should be on the first tab, but you will need to scroll down to find it.
    - Set this to “no RF”
    - As of the DUST upgrade, this will cause conflicts with other items in the list, so set the following parameters:
        - SPAIR spectro pulse shape = hs_500_400_100
		- ENCASE pulse choice = sg_1246_200_0
  	    - RFE broadband adiabatic 3D inv shape = hs3_4_6
        - Double Basing pulse shape = dubbase3 
    - Click “Apply”. The button should turn grey. If it doesn’t, the changes weren’t applied.
- After functional scans, go back to “Scan Control Parameters” and reset "restore factory defaults"

Analysis procedure:
- Obtain raw data.
- Calculate the phase image from the real and imaginary components.
- Use magnitude only to estimate g factor.
- Specify the noise volume during NORDIC (i.e., don’t estimate it based on the magnitude image).
- Continue the analysis as for any other fMRI dataset.

"pipeline.py" is a controller script that can be run, calling each function in turn to produce the entire analysis (currently just resting-state, not including any experimental stimulus-driven data).

"test_NORDIC.py" applies many different preprocessing configurations to the same dataset, which must have BIDS structure.

"run_NORDIC.py" applies one particular preprocessing configuration to a dataset, and is best if you just want to implement this without exploring the different options yourself.

