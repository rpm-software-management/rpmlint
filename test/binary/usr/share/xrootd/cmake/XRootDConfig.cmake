################################################################################
# Module for locating XRootD.
#
#   XROOTD_FOUND
#     Indicates whether the library has been found.
#
#   XROOTD_INCLUDE_DIRS
#      Specifies XRootD include directory.
#
#   XROOTD_LIBRARIES
#     Specifies XRootD libraries that should be passed to target_link_libararies.
#
#   XROOTD_<COMPONENT>_LIBRARIES
#     Specifies the libraries of a specific <COMPONENT>
#
#   XROOTD_<COMPONENT>_FOUND
#     Indicates whether the specified <COMPONENT> was found.
#
#   List of components: CLIENT, UTILS, SERVER, POSIX, HTTP and SSI
################################################################################

################################################################################
# Make sure all *_FOUND variables are intialized to FALSE
################################################################################
SET( XROOTD_FOUND         FALSE )
SET( XROOTD_CLIENT_FOUND  FALSE )
SET( XROOTD_UTILS_FOUND   FALSE )
SET( XROOTD_SERVER_FOUND  FALSE )
SET( XROOTD_POSIX_FOUND   FALSE )
SET( XROOTD_HTTP_FOUND    FALSE )
SET( XROOTD_SSI_FOUND     FALSE )

################################################################################
# Set XRootD include paths
################################################################################
FIND_PATH( XROOTD_INCLUDE_DIRS XrdVersion.hh
  HINTS
  ${XROOTD_DIR}
  $ENV{XROOTD_DIR}
  /usr
  /opt/xrootd
  PATH_SUFFIXES include/xrootd
  PATHS /opt/xrootd
)

IF( NOT "${XROOTD_INCLUDE_DIRS}" STREQUAL "XROOTD_INCLUDE_DIRS-NOTFOUND" )
  SET( XROOTD_FOUND TRUE )
  SET( XROOTD_INCLUDE_DIRS "${XROOTD_INCLUDE_DIRS};${XROOTD_INCLUDE_DIRS}/private" )
ENDIF()

IF( NOT XROOTD_FOUND )
  LIST( APPEND _XROOTD_MISSING_COMPONENTS XROOTD_FOUND )
ENDIF()

################################################################################
# XRootD client libs
#  - libXrdCl
################################################################################
FIND_LIBRARY( XROOTD_CLIENT_LIBRARIES XrdCl
  HINTS
  ${XROOTD_DIR}
  $ENV{XROOTD_DIR}
  /usr
  /opt/xrootd
  PATH_SUFFIXES lib lib64
)

IF( NOT "${XROOTD_CLIENT_LIBRARIES}" STREQUAL "XROOTD_CLIENT_LIBRARIES-NOTFOUND" )
  SET( XROOTD_CLIENT_FOUND TRUE )
  LIST( APPEND XROOTD_LIBRARIES ${XROOTD_CLIENT_LIBRARIES} )
ENDIF()

IF( XRootD_FIND_REQUIRED_CLIENT AND NOT XROOTD_CLIENT_FOUND )
  MESSAGE( "XRootD client required but not found!" )
  LIST( APPEND _XROOTD_MISSING_COMPONENTS XROOTD_CLIENT_FOUND )
  SET( XROOTD_FOUND FALSE )
ENDIF()

################################################################################
# XRootD utils libs
#  - libXrdUtils
################################################################################
FIND_LIBRARY( XROOTD_UTILS_LIBRARIES XrdUtils
  HINTS
  ${XROOTD_DIR}
  $ENV{XROOTD_DIR}
  /usr
  /opt/xrootd
  PATH_SUFFIXES lib lib64
)

IF( NOT "${XROOTD_UTILS_LIBRARIES}" STREQUAL "XROOTD_UTILS_LIBRARIES-NOTFOUND" )
  SET( XROOTD_UTILS_FOUND TRUE )
  LIST( APPEND XROOTD_LIBRARIES ${XROOTD_UTILS_LIBRARIES} )
ENDIF()

IF( XRootD_FIND_REQUIRED_UTILS AND NOT XROOTD_UTILS_FOUND )
  MESSAGE( "XRootD utils required but not found!" )
  LIST( APPEND _XROOTD_MISSING_COMPONENTS XROOTD_UTILS_FOUND )
  SET( XROOTD_FOUND FALSE )
ENDIF()

################################################################################
# XRootD server libs
#  - libXrdServer
################################################################################
FIND_LIBRARY( XROOTD_SERVER_LIBRARIES XrdServer
  HINTS
  ${XROOTD_DIR}
  $ENV{XROOTD_DIR}
  /usr
  /opt/xrootd
  PATH_SUFFIXES lib lib64
)

IF( NOT "${XROOTD_SERVER_LIBRARIES}" STREQUAL "XROOTD_SERVER_LIBRARIES-NOTFOUND" )
  SET( XROOTD_SERVER_FOUND TRUE )
  LIST( APPEND XROOTD_LIBRARIES ${XROOTD_SERVER_LIBRARIES} )
ENDIF()

IF( XRootD_FIND_REQUIRED_SERVER AND NOT XROOTD_SERVER_FOUND )
  MESSAGE( "XRootD server required but not found!" )
  LIST( APPEND _XROOTD_MISSING_COMPONENTS XROOTD_SERVER_FOUND )
  SET( XROOTD_FOUND FALSE )
ENDIF()

################################################################################
# XRootD posix libs
#  - libXrdPosix
#  - libXrdPosixPreload
################################################################################
FIND_LIBRARY( XROOTD_POSIX_LIBRARY XrdPosix
  HINTS
  ${XROOTD_DIR}
  $ENV{XROOTD_DIR}
  /usr
  /opt/xrootd
  PATH_SUFFIXES lib lib64
)

FIND_LIBRARY( XROOTD_POSIX_PRELOAD_LIBRARY XrdPosixPreload
  HINTS
  ${XROOTD_DIR}
  $ENV{XROOTD_DIR}
  /usr
  /opt/xrootd
  PATH_SUFFIXES lib lib64
)

IF( NOT "${XROOTD_POSIX_LIBRARY}" STREQUAL "XROOTD_POSIX_LIBRARY-NOTFOUND" )
  IF( NOT "${XROOTD_POSIX_PRELOAD_LIBRARY}" STREQUAL "XROOTD_POSIX_PRELOAD_LIBRARY-NOTFOUND" )
    SET( XROOTD_POSIX_LIBRARIES ${XROOTD_POSIX_LIBRARY} ${XROOTD_POSIX_PRELOAD_LIBRARY} )
    SET( XROOTD_POSIX_FOUND TRUE )  
    LIST( APPEND XROOTD_LIBRARIES ${XROOTD_POSIX_LIBRARIES} )
  ENDIF()
ENDIF()

IF( XRootD_FIND_REQUIRED_POSIX AND NOT XROOTD_POSIX_FOUND )
  MESSAGE( "XRootD posix required but not found!" )
  LIST( APPEND _XROOTD_MISSING_COMPONENTS XROOTD_POSIX_FOUND )
  SET( XROOTD_FOUND FALSE )
ENDIF()

################################################################################
# XRootD HTTP (XrdHttp) libs
#  - libXrdHtppUtils
################################################################################
FIND_LIBRARY( XROOTD_HTTP_LIBRARIES XrdHttpUtils
  HINTS
  ${XROOTD_DIR}
  $ENV{XROOTD_DIR}
  /usr
  /opt/xrootd
  PATH_SUFFIXES lib lib64
)

IF( NOT "${XROOTD_HTTP_LIBRARIES}" STREQUAL "XROOTD_HTTP_LIBRARIES-NOTFOUND" )
  SET( XROOTD_HTTP_FOUND TRUE )
  LIST( APPEND XROOTD_LIBRARIES ${XROOTD_HTTP_LIBRARIES} )
ENDIF()

IF( XRootD_FIND_REQUIRED_HTTP AND NOT XROOTD_HTTP_FOUND )
  MESSAGE( "XRootD http required but not found!" )
  LIST( APPEND _XROOTD_MISSING_COMPONENTS XROOTD_HTTP_FOUND )
  SET( XROOTD_FOUND FALSE )
ENDIF()

################################################################################
# XRootD SSI libs
#  - XrdSsiLib
#  - XrdSsiShMap
################################################################################
FIND_LIBRARY( XROOTD_SSI_LIBRARY XrdSsiLib
  HINTS
  ${XROOTD_DIR}
  $ENV{XROOTD_DIR}
  /usr
  /opt/xrootd
  PATH_SUFFIXES lib lib64
)

FIND_LIBRARY( XROOTD_SSI_SHMAP_LIBRARY XrdSsiShMap
  HINTS
  ${XROOTD_DIR}
  $ENV{XROOTD_DIR}
  /usr
  /opt/xrootd
  PATH_SUFFIXES lib lib64
)

IF( NOT "${XROOTD_SSI_LIBRARY}" STREQUAL "XROOTD_SSI_LIBRARY-NOTFOUND" )
  IF( NOT "${XROOTD_SSI_SHMAP_LIBRARY}" STREQUAL "XROOTD_SSI_SHMAP_LIBRARY-NOTFOUND" )
    SET( XROOTD_SSI_LIBRARIES ${XROOTD_SSI_LIBRARY} ${XROOTD_SSI_SHMAP_LIBRARY} )
    SET( XROOTD_SSI_FOUND TRUE )
    LIST( APPEND XROOTD_LIBRARIES ${XROOTD_SSI_LIBRARIES} )
  ENDIF()
ENDIF()

IF( XRootD_FIND_REQUIRED_SSI AND NOT XROOTD_SSI_FOUND )
  MESSAGE( "XRootD ssi required but not found!" )
  LIST (APPEND _XROOTD_MISSING_COMPONENTS XROOTD_SSI_FOUND )
  SET( XROOTD_FOUND FALSE )
ENDIF()

################################################################################
# Utility variables for plug-in development
################################################################################
IF( XROOTD_FOUND )
  SET( XROOTD_PLUGIN_VERSION 5 )
ENDIF()

################################################################################
# Set up the XRootD find module
################################################################################

IF( XRootD_FIND_REQUIRED )
  INCLUDE( FindPackageHandleStandardArgs )
  FIND_PACKAGE_HANDLE_STANDARD_ARGS( XRootD
    REQUIRED_VARS  XROOTD_INCLUDE_DIRS  ${_XROOTD_MISSING_COMPONENTS}
  )
ENDIF()

