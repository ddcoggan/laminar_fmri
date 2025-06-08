# laminar_fmri
Preprocessing pipeline for high-res fMRI at the 7T Phillips Achieva scanner in the Human Imaging department of the Vanderbilt Institute of Imaging Science.

This pipeline involves NORDIC preprocessing, based on the following paper: https://www.nature.com/articles/s41467-021-25431-8, and requires their MATLAB package. In this implementation, their package is called by python using the MATLAB engine. In practice, I have found that data quality (measured primarily based on tSNR in resting-state scans) is dependent on whether the magnitude and / or phase components are obtained directly from the scanner or  calculated from the real/imaginary components output by the scanner. The best configuration I found is to use the magnitude component from the scanner, and to calculate the phase component from the real and imaginary components. The dataset must have BIDS structure for the python modules to work.

Scanning procedure:
-	Run fieldmap and anatomical scans as normal.
-	Make sure each functional scan has 1 extra dynamic than the stimulus procedure, and saves out the Magnitude, Real, and Imaginary components.
-	Before the first functional scan, right click in gray area below scan list, go to “Scan Control Parameters”
-	Set “Dyn. Noise Scan” to “no RF” (you will need to scroll down to find it) and click "Apply", confirm that the "Apply" button is now grayed out.
-	Note: If it isn’t grayed out, the changes weren’t applied. This has occurred in the past due to conflicts with other parameters in v2.0 of the software, but seems to have been resolved as of v2.5. If these recur, set the following parameters (in the same window):
	- SPAIR spectro pulse shape = hs_500_400_100
	- ENCASE pulse choice = sg_1246_200_0
	- RFE broadband adiabatic 3D inv shape = hs3_4_6
	- Double Basing pulse shape = dubbase3 
- After functional scans, go back to “Scan Control Parameters” and reset "restore factory defaults". Close the pop up window and confirm that the "Dyn. Noise Scan" option is no longer "no RF".

Analysis procedure:
- Obtain raw data.
- Calculate the phase image from the real and imaginary components.
- Use magnitude only to estimate g factor.
- Specify the noise volume during NORDIC (i.e., don’t estimate it based on the magnitude image).
- Continue the analysis as for any other fMRI dataset.

"pipeline.py" is a controller script that can be run, calling each function in turn to produce the entire analysis (currently just resting-state, not including any experimental stimulus-driven data).

"test_NORDIC.py" applies many different preprocessing configurations to the same dataset.

"run_NORDIC.py" applies one particular preprocessing configuration to a dataset, and is best if you just want to implement this without exploring the different options yourself.

