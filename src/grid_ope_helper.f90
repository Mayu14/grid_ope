program grid_ope_helper
    implicit none
    integer :: inum_args, ilength, istatus
    character, allocatable :: cargs(:)
    intrinsic :: command_argument_count, get_command_argument

    character(len=64) :: cmode, cparameter, cfilename, ccasename
    integer :: iparameter
    
    inum_args = command_argument_count()
    if ( inum_args == 0 ) then
        call usage()
    end if

    call get_command_argument(1, cmode, status = istatus)
    if ( istatus /= 0) then
        write(6,*) 'Error: cmd line args cannot read'
        stop 1
    end if
    
    if ( trim(adjustl(cmode)) == '--re_numbering_face' ) then
        if ( inum_args /= 4 ) then
            write(6,*) 'Error: '//trim(adjustl(cmode))//' is needed 3 args'
            call usage() 
        end if
        call get_command_argument(2, cparameter)
        read(cparameter, *) iparameter 

        call get_command_argument(3, cfilename)
        call get_command_argument(4, ccasename)
        call re_numbering_face(iparameter, cfilename, ccasename, 3)
    
    else if ( trim(adjustl(cmode)) == '--re_numbering_line' ) then
        if ( inum_args /= 4 ) then
            write(6,*) 'Error: '//trim(adjustl(cmode))//' is needed 3 args'
            call usage() 
        end if
        call get_command_argument(2, cparameter)
        read(cparameter, *) iparameter 

        call get_command_argument(3, cfilename)
        call get_command_argument(4, ccasename)
        call re_numbering_face(iparameter, cfilename, ccasename, 2)

    else
        write(6,*) 'Error: mode: '//trim(adjustl(cmode))//' is not supported.'
        stop 1
    end if

    
    stop 0

contains
        subroutine usage()
            implicit none
            write(6,*) 'Usage: grid_ope_helper'
            write(6,*) './grid_ope_helper [options]'
            write(6,*) '  options'
            write(6,*) ''
            write(6,*) '    --re_numbering_face : check the overlapped face element'
            write(6,*) '      $2: tmp_num_faces; $3: file_name of tmp_faces; $4: casename (ex. IGRID)'
            write(6,*) ''
            write(6,*) '    --re_numbering_line : check the overlapped line element'
            write(6,*) '      $2: tmp_num_lines; $3: file_name of tmp_lines; $4: casename (ex. IGRID)'
            write(6,*) ''
            stop 0
        end subroutine usage


        subroutine re_numbering_face(itmp_num_face, cfilename, ccasename, ipts_per_element)
            implicit none
            integer, intent(in) :: itmp_num_face, ipts_per_element
            character(len=64), intent(in) :: cfilename, ccasename
            character(len=64) :: creadline
            integer, allocatable :: itmp_faces(:, :)
            integer, allocatable :: ire_numbering_face(:)

            integer :: iface, ipts, new_face_id = 0
            
            integer :: face_id1, face_id2
            integer :: same_face

            if ( ipts_per_element < 2 .or. ipts_per_element > 3 ) then
                write(6,*) "Error: variable ipts_per_element has invalid value"
                stop 1
            end if

            allocate(itmp_faces(0:itmp_num_face, 0:ipts_per_element), ire_numbering_face(0:itmp_num_face))

            open(unit = 1, file=trim(adjustl(cfilename)), status = 'unknown')
                do iface = 0, itmp_num_face-1
                    read(1,*) (itmp_faces(iface, ipts),ipts=0,ipts_per_element-1)                    
                end do
            close(1)
            
            ire_numbering_face = -1

            do face_id1 = 0, itmp_num_face-1
                if (ire_numbering_face(face_id1) /= -1) then
                    cycle
                end if

                ire_numbering_face(face_id1) = new_face_id
                do face_id2 = 0, itmp_num_face-1
                    if (face_id1 >= face_id2) then
                        cycle
                    end if

                    same_face = 1
                    do ipts=0, ipts_per_element-1
                        if (itmp_faces(face_id1, ipts) /= itmp_faces(face_id2, ipts)) then
                            same_face = 0
                            exit
                        end if
                    end do

                    if ( same_face == 1) then
                        ire_numbering_face(face_id2) = new_face_id
                    end if
                end do
                new_face_id = new_face_id + 1
                if (mod(face_id1, 1000) == 0 ) then
                    write(6,*) face_id1, itmp_num_face
                end if
            end do

            if ( ipts_per_element == 3 ) then
                open(unit = 1, file='data/'//trim(adjustl(ccasename))//'_re_numbering_face.txt', status = 'unknown')
            else if ( ipts_per_element == 2 ) then
                open(unit = 1, file='data/'//trim(adjustl(ccasename))//'_re_numbering_line.txt', status = 'unknown')
            else
                stop 1
            end if

            do iface = 0, itmp_num_face-1
                write(1,"(1x,i8)") ire_numbering_face(iface)
            end do
            close(1)

            return
        end subroutine re_numbering_face

end program grid_ope_helper