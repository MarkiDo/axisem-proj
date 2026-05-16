! Proc   2: Header for mesh information to run static solver
! created by the mesher on 05/09/2026, at 23h 59min
 
!:::::::::::::::::::: Input parameters :::::::::::::::::::::::::::
!   Background model     :            prem_iso
!   Dominant period [s]  :   50.0000
!   Elements/wavelength  :    1.5000
!   Courant number       :    0.6000
!   Coarsening levels    :         3
!:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
 
 integer, parameter ::         npol =         4  !            polynomial order
 integer, parameter ::        nelem =      3072  !                   proc. els
 integer, parameter ::       npoint =     76800  !               proc. all pts
 integer, parameter ::    nel_solid =      2664  !             proc. solid els
 integer, parameter ::    nel_fluid =       408  !             proc. fluid els
 integer, parameter :: npoint_solid =     66600  !             proc. solid pts
 integer, parameter :: npoint_fluid =     10200  !             proc. fluid pts
 integer, parameter ::  nglob_fluid =      6725  !            proc. flocal pts
 integer, parameter ::     nel_bdry =        72  ! proc. solid-fluid bndry els
 integer, parameter ::        ndisc =        12  !   # disconts in bkgrd model
 integer, parameter ::   nproc_mesh =         2  !        number of processors
 integer, parameter :: lfbkgrdmodel =         8  !   length of bkgrdmodel name
 
!:::::::::::::::::::: Output parameters ::::::::::::::::::::::::::
!   Time step [s]        :    0.1432
!   Min(h/vp),dt/courant :    0.8050    0.9548
!   max(h/vs),T0/wvlngth :   32.1071   33.3333
!   Inner core r_min [km]:  927.8372
!   Max(h) r/ns(icb) [km]:   79.9470
!   Max(h) precalc.  [km]:   89.2151
!:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
 
