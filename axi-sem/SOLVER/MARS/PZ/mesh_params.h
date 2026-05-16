! Proc   2: Header for mesh information to run static solver
! created by the mesher on 05/10/2026, at 00h 29min
 
!:::::::::::::::::::: Input parameters :::::::::::::::::::::::::::
!   Background model     :            external
!   Dominant period [s]  :   50.0000
!   Elements/wavelength  :    1.5000
!   Courant number       :    0.6000
!   Coarsening levels    :         3
!:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
 
 integer, parameter ::         npol =         4  !            polynomial order
 integer, parameter ::        nelem =     21472  !                   proc. els
 integer, parameter ::       npoint =    536800  !               proc. all pts
 integer, parameter ::    nel_solid =     13200  !             proc. solid els
 integer, parameter ::    nel_fluid =      8272  !             proc. fluid els
 integer, parameter :: npoint_solid =    330000  !             proc. solid pts
 integer, parameter :: npoint_fluid =    206800  !             proc. fluid pts
 integer, parameter ::  nglob_fluid =    133069  !            proc. flocal pts
 integer, parameter ::     nel_bdry =       176  ! proc. solid-fluid bndry els
 integer, parameter ::        ndisc =         9  !   # disconts in bkgrd model
 integer, parameter ::   nproc_mesh =         2  !        number of processors
 integer, parameter :: lfbkgrdmodel =         8  !   length of bkgrdmodel name
 
!:::::::::::::::::::: Output parameters ::::::::::::::::::::::::::
!   Time step [s]        :    0.0017
!   Min(h/vp),dt/courant :    0.0097    0.0115
!   max(h/vs),T0/wvlngth :   31.7284   33.3333
!   Inner core r_min [km]: 1603.3204
!   Max(h) r/ns(icb) [km]:   15.3331
!   Max(h) precalc.  [km]:  127.4218
!:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
 
