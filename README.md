# ABACUS+DPMD+Dflow：Quick Test Semiconductor Melting Point Properties with Candela Installation and Usage Instructions
# 1. Introduction
### Introduction to ABACUS Molecular Dynamics

ABACUS's molecular dynamics functionality supports both first-principles molecular dynamics (FPMD) method and classical Lennard-Jones (LJ potential) molecular dynamics simulation. In addition, ABACUS also supports Deep Potential Molecular Dynamics (DPMD) method, which requires compiling the DeePMD-kit software package and linking the dynamic library when compiling the atomic calculation software.

After testing, using the image registry.dp.tech/dptech/prod-12058/abacus-deepmd-kit-candela:abacus-deepmd-kit-candela_v1.01, you can directly run the tasks of this tutorial from the command line.

If readers use the dflow script provided below to submit tasks, there is no need to install ABACUS and compile the interface locally, nor to install and compile Candela. Only the ABACUS input file needs to be prepared.
### Introduction to Melting Point Testing Methods
#### Direct Heating Method
- The melting process of a material is observed by heating it directly. At the beginning of the simulation, the atoms or molecules in the system are placed at an initial temperature and the temperature is gradually increased by applying heat. As the temperature increases, the interactions between the atoms or molecules change until the melting point is reached. By monitoring the changes in the position, energy, and other physical properties of the atoms or molecules in the system, the melting point of the material can be determined.

- The improved direct heating method is used in this tutorial. In the traditional direct heating method, where the initial and final temperatures are set differently, each point in the process is in a non-equilibrium state, making it difficult to accurately describe the state of the material at that temperature. Therefore, in this method, the NPT ensemble is used to simulate the system at each temperature for tens of picoseconds to reach an equilibrium state, and the mean square displacement and diffusion coefficient are output to determine the state of the material. However, without using dflow, this method requires manually modifying the parameters and submitting the tasks multiple times, which is cumbersome. The provided dflow script can automate the process to some extent.
#### Two-Phase Method
- The transformation process between the solid and liquid states is observed. At the beginning of the simulation, the atoms or molecules in the system are placed at a low temperature and form a solid structure. Then, by gradually increasing the temperature, the interactions between the atoms or molecules change, causing the material to transition from the solid state to the liquid state. By monitoring the changes in the atomic or molecular structure, density, energy, and other physical properties of the system, the melting point of the material can be determined.
#### Z-Method
- The Z-method is a thermal analysis technique used in molecular dynamics simulations, combining the advantages of the direct heating method and the two-phase method. Continuously changing the initial energy value of the NVE ensemble, after running for a period of time, a balanced T and P value will be obtained, drawn as an isocapacity line and presented as a z-type. The lower vertex of the z-type is the melting point temperature, and the upper vertex is the superheat temperature.
- # 2. Preparation
- ## Environment Configuration
### Online Deployment (for notebook testing only)
Install dflow and Bohrium client:
! pip install pydflow -U -i https://pypi.tuna.tsinghua.edu.cn/simple
! pip install lbg -U -i https://pypi.tuna.tsinghua.edu.cn/simple
# Example download link
## Prepare input file INPUT
The example system uses cubic ZnS, and its experimental melting point is 1350 ℃. In this case, we use a simple direct heating method. Previous LAMMPS simulations on a 216-atom system showed that the melting point of ZnS is between 1967~2009K, while the experimental melting point is 1623K, which is about 370K higher.

We can modify the parameter md_tfirst and run the appropriate number of MD steps at each temperature (set by md_nstep, which is an empirical value) to obtain the equilibrium structure at that temperature. When the melting point is unknown, we can select temperature points at equal intervals for testing. After determining the range where the melting point is located, we can insert temperature points at equal intervals within this range to further narrow down the range of melting point testing results. It is important to note that the initial temperature should not exceed the upper limit of the DPGEN sampling temperature.

The following is an example of the file content:
'''
INPUT_PARAMETERS
suffix              DPMD-melting
calculation         md
esolver_type        dp
pot_file            ./frozen_model.pb
ntype               2
md_nstep            25000
md_type             npt
md_pmode            iso
md_pcouple          xyz
md_pfirst           0.001
md_pfreq            0.0005
md_pchain           3
md_tchain           3
md_dt               2
md_tfirst           2500
md_seed             2121491
md_tfreq            0.005
md_dumpfreq         1
md_restartfreq      1000
init_vel            0
dump_force          1
dump_vel            1
dump_virial         1
'''
____

These parameters are all explained in the ABACUS online documentation and are briefly summarized here:

- **calculation**: Set the ABACUS calculation type, set to md for molecular dynamics simulation.
- **esolver_type**: Specify the calculation of system energy given atomic positions, default is Kohn-Sham density functional theory (ksdft), can also be set to LJ potential (lj) or deep potential (dp). In theory, all esolver_type can be used for MD calculation.
- **pot_file**: Path to the potential function file.
- **md_nstep**: Total number of steps for MD simulation.
- **md_type**: Type of MD algorithm, default is NVT for canonical ensemble, this example selects NPT for NVE microcanonical ensemble.
- **md_dt**: Time step for each MD calculation step (in fs), together with md_nstep determines the total duration of MD simulation.
- **md_tfirst**: Initial temperature of the MD system (in K).
- **md_tchain**: Default value is 1 for ABACUS, 3 for LAMMPS.
- **md_tfreq**: Controls the rate of temperature change in MD simulation, recommended value is 1/40/dt. Relationship with Tdamp in LAMMPS: 1/(1000*Tdamp)fs-1.
- **md_seed**: Whether the initial velocities are random.
- **md_pfirst**: Initial pressure of the MD system (in kbar).
- **md_pfreq**: Controls the rate of pressure change in MD simulation, recommended value is 1/400/dt. Relationship with Pdamp in LAMMPS: 1/(1000*Pdamp)fs-1.
- **md_pchain**: Default value is 1 for ABACUS, 3 for LAMMPS.
- **md_pmode**: Method of applying pressure in MD simulation.
- **md_pcouple**: Controls the independence of box scaling direction in MD simulation.
- **md_dumpfreq**: Output frequency of atomic and cell information in the MD output file MD_dump.
- **md_restartfreq**: Output frequency of structure file STRU_MD_${istep}, update frequency of MD restart file Restart_md.dat.
- ## Preparing the structure file STRU for atomic systems
- The files that describe the atomic structure required for this step are:

    *.cif

The structure files can be downloaded from multiple sources. In this case, we mainly download cif files from the materials project website. The semiconductor used may correspond to multiple atomic configurations. Previous LAMMPS simulations have shown that the selection of the initial configuration has little impact on the results, as the equilibrium structure of the system at this temperature exists. The choice of configurations depends on the system and properties being studied. Generally, structures that may appear in the temperature and pressure range of interest can be selected, or the simplest cubic structure can be used. In this case, a cubic ZnS structure is used for demonstration purposes.

- 
Considering the size effect, you can first use VESTA to enlarge the lattice of the cif file to the desired size.

After obtaining the cif file, you can use the following methods to convert the cif file to STRU file:
! git clone https://gitlab.com/1041176461/ase-abacus.git
%cd ase-abacus
! python3 setup.py install
%cd ../ABACUS-dflow/
! ls
cif to STRU
'''
from ase.io import read, write
from pathlib import Path

cs_dir = './'
cs_vasp = Path(cs_dir, 'ZnS.cif') # Change to your own cif file name
cs_atoms = read(cs_vasp, format='cif')
cs_stru = Path(cs_dir, 'STRU')
write(cs_stru, cs_atoms, format='abacus')
'''
Run the above python script to convert cif to STRU file required by ABACUS.
Note: You can determine whether the keyword "type_map" exists in the DP potential file using the following command.
! strings ./ABACUS-workflow/DPMD/frozen_model.pb | grep type_map
If the keyword type_map exists, ABACUS will automatically match the atomic species order in the STRU and DP potential files.

Otherwise, the atomic species and order in STRU must be consistent with those in the DP potential files.
## Prepare DP potential function file frozen_model.pb
The selected DP potential function in this case is derived from ABACUS+DPGEN. If readers are interested in the generation method of the potential function, they can refer to the ABACUS Chinese documentation tutorial.
## Preparation for Candela

Note: This section is not relevant to the task execution and is only for readers who need to install Candela. You can skip this section if you are following the tasks in order.
### Introduction
Candela, short for Collection of ANalysis DEsigned for Large-scale Atomic simulations, currently supports the analysis of molecular dynamics trajectories from QE, ABACUS, LAMMPS, and VASP. The Github homepage can be found at: https://github.com/MCresearch/Candela

For more information on using ABACUS+Candela, please refer to: https://mcresearch.gitee.io/abacus-user-guide/abacus-candela.html

We use Candela for post-processing tasks.
### Environment Preparation
The image "registry.dp.tech/dptech/prod-12058/abacus-deepmd-kit-candela:abacus-deepmd-kit-candela_v1.00" provided in the dflow script has already installed Candela. You can directly run the command "candela" in the command line.

If Candela is not installed in the runtime environment, manual installation is required. Follow the steps below:
! git clone https://github.com/MCresearch/Candela.git
! cd Candela && make CXX=g++ TEST=ON
At this time, Candela compilation is completed and the serial version can be run, which is sufficient for calculating MSD for general systems.

After preparing the input file and MD_dump file, go to the path where the input file is located and run the command line directly to obtain the output result.
Note:

If using the Intel Oneapi compiler, the compilation can be done using the command "make -j4". After the compilation is completed, the executable file "candela" can be found in the bin directory.

If using other compilers, you need to modify the corresponding CXX in the Makefile.vars under the Candela directory.
### Input File Preparation
The example INPUT file is as follows:

(Note that the unit of msd_dt here is ps, which needs to be modified to match the md_dt in the ABACUS INPUT file)
```
calculation  msd # Pair Distribution Function.
system ZnS
geo_in_type  ABACUS
geo_directory MD_dump
geo_1        1
geo_2        2000
geo_interval 1
geo_ignore   300

ntype        2        # number of different types of atoms.
natom        216   # total number of atoms.
natom1       108   #Zn
natom2       108   #S
id1          Zn
id2          S
msd_dt       0.002
```
# 3. Building and Running Dflow

## Flowchart
Prepare input file - [Modify md_tfisrt - Submit task - Post-processing with candela to obtain MSD]

For testing the melting point properties of semiconductors, it is most flexible to execute the parts inside the box in parallel using dflow. Here, a Slices OP is used to implement this.

The improved flowchart is shown below:

![image.png](https://bohrium.oss-cn-zhangjiakou.aliyuncs.com/article/12058/38970301ae5149a3b11fe5bc684c1397/Ldimw09TcX1HW5l9IJMWhQ.png)

## Dflow Code
Note: The number of temperature points NUM needs to be manually modified. The input file is a packaged ABACUS input folder (named DPMD here) and md_tfirst_file. This script should be executed in the same directory. This code only needs to be run once. If the example python code has been run, there is no need to repeat the subsequent steps.
%cd ../ABACUS-dflow/ABACUS-workflow

