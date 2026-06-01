! Proc   2: Header for mesh information to run static solver
! created by the mesher on 05/27/2026, at 13h 17min
 
!:::::::::::::::::::: Input parameters :::::::::::::::::::::::::::
!   Background model     :            external
!   Dominant period [s]  :    1.0000
!   Elements/wavelength  :    1.5000
!   Courant number       :    0.4000
!   Coarsening levels    :         3
!:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
 
 integer, parameter ::         npol =         4  !            polynomial order
 integer, parameter ::        nelem =   2776064  !                   proc. els
 integer, parameter ::       npoint =  69401600  !               proc. all pts
 integer, parameter ::    nel_solid =   2076672  !             proc. solid els
 integer, parameter ::    nel_fluid =    699392  !             proc. fluid els
 integer, parameter :: npoint_solid =  51916800  !             proc. solid pts
 integer, parameter :: npoint_fluid =  17484800  !             proc. fluid pts
 integer, parameter ::  nglob_fluid =  11197673  !            proc. flocal pts
 integer, parameter ::     nel_bdry =      2048  ! proc. solid-fluid bndry els
 integer, parameter ::        ndisc =         6  !   # disconts in bkgrd model
 integer, parameter ::   nproc_mesh =         2  !        number of processors
 integer, parameter :: lfbkgrdmodel =         8  !   length of bkgrdmodel name
 
!:::::::::::::::::::: Output parameters ::::::::::::::::::::::::::
!   Time step [s]        :    0.0053
!   Min(h/vp),dt/courant :    0.0731    0.0530
!   max(h/vs),T0/wvlngth :    0.6669    0.6667
!   Inner core r_min [km]: 1079.1394
!   Max(h) r/ns(icb) [km]:    2.6225
!   Max(h) precalc.  [km]:    2.6295
!:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
 
