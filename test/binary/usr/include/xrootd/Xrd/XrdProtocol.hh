#ifndef __XrdProtocol_H__
#define __XrdProtocol_H__
/******************************************************************************/
/*                                                                            */
/*                        X r d P r o t o c o l . h h                         */
/*                                                                            */
/*(c) 2004-18 By the Board of Trustees of the Leland Stanford, Jr., University*/
/*   Produced by Andrew Hanushevsky for Stanford University under contract    */
/*              DE-AC02-76-SFO0515 with the Department of Energy              */
/*                                                                            */
/* This file is part of the XRootD software suite.                            */
/*                                                                            */
/* XRootD is free software: you can redistribute it and/or modify it under    */
/* the terms of the GNU Lesser General Public License as published by the     */
/* Free Software Foundation, either version 3 of the License, or (at your     */
/* option) any later version.                                                 */
/*                                                                            */
/* XRootD is distributed in the hope that it will be useful, but WITHOUT      */
/* ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or      */
/* FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public       */
/* License for more details.                                                  */
/*                                                                            */
/* You should have received a copy of the GNU Lesser General Public License   */
/* along with XRootD in a file called COPYING.LESSER (LGPL license) and file  */
/* COPYING (GPL license).  If not, see <http://www.gnu.org/licenses/>.        */
/*                                                                            */
/* The copyright holder's institutional names and contributor's names may not */
/* be used to endorse or promote products derived from this software without  */
/* specific prior written permission of the institution or contributor.       */
/******************************************************************************/

#include "Xrd/XrdJob.hh"
 
/******************************************************************************/
/*                    X r d P r o t o c o l _ C o n f i g                     */
/******************************************************************************/
  
// The following class is passed to the XrdgetProtocol() and XrdgetProtocolPort()
// functions to properly configure the protocol. This object is not stable and 
// the protocol must copy out any values it desires to keep. It may copy the 
// whole object using the supplied copy constructor.

class XrdSysError;
union XrdNetSockAddr;
class XrdOucEnv;
class XrdOucString;
class XrdBuffManager;
class XrdInet;
class XrdScheduler;
class XrdStats;
class XrdTlsContext;

struct sockaddr;

class XrdProtocol_Config
{
public:

// The following pointers may be copied; they are stable.
//
XrdSysError    *eDest;       // Stable -> Error Message/Logging Handler
XrdInet        *NetTCP;      // Stable -> Network Object    (@ XrdgetProtocol)
XrdBuffManager *BPool;       // Stable -> Buffer Pool Manager
XrdScheduler   *Sched;       // Stable -> System Scheduler
XrdStats       *Stats;       // Stable -> System Statistics (@ XrdgetProtocol)
XrdOucEnv      *theEnv;      // Stable -> Additional environmental information
void           *rsvd0;

// The following information must be duplicated; it is unstable.
//
char            *ConfigFN;     // -> Configuration file
int              Format;       // Binary format of this server
int              Port;         // Port number
int              WSize;        // Window size for Port
int              rsvd1;
const char      *AdmPath;      // Admin path
int              AdmMode;      // Admin path mode
int              xrdFlags;
static const int admPSet    = 0x00000001;  // The adminppath was set via cli

const char      *myInst;       // Instance name
const char      *myName;       // Host name
const char      *myProg;       // Program name
union {
const
XrdNetSockAddr  *urAddr;       // Host Address (the actual structure/union)
const
struct sockaddr *myAddr;       // Host address
      };
int              ConnMax;      // Max connections
int              readWait;     // Max milliseconds to wait for data
int              idleWait;     // Max milliseconds connection may be idle
int              argc;         // Number of arguments
char           **argv;         // Argument array (prescreened)
char             DebugON;      // True if started with -d option
char             rsvd3[7];
int              hailWait;     // Max milliseconds to wait for data after accept
int              tlsPort;      // Default TLS port (0 if not specified)
XrdTlsContext   *tlsCtx;       // Stable -> TLS Context (0 if not initialized)
XrdOucString    *totalCF;      // Stable -> total config after full init

                 XrdProtocol_Config(XrdProtocol_Config &rhs) =delete;
                 XrdProtocol_Config() : rsvd0(0), rsvd1(0)
                                        {memset(rsvd3, 0, sizeof(rsvd3));}
                ~XrdProtocol_Config() {}
};

/******************************************************************************/
/*                           X r d P r o t o c o l                            */
/******************************************************************************/

// This class is used by the Link object to process the input stream on a link.
// At least one protocol object exists per Link object. Specific protocols are 
// derived from this pure abstract class since a link can use one of several 
// protocols. Indeed, startup and shutdown are handled by specialized protocols.

// System configuration obtains an instance of a protocol by calling
// XrdgetProtocol(), which must exist in the shared library.
// This instance is used as the base pointer for Alloc(), Configure(), and
// Match(). Unfortuantely, they cannot be static given the silly C++ rules.

class XrdLink;
  
class XrdProtocol : public XrdJob
{
public:

// Match()     is invoked when a new link is created and we are trying
//             to determine if this protocol can handle the link. It must
//             return a protocol object if it can and NULL (0), otherwise.
//
virtual XrdProtocol  *Match(XrdLink *lp) = 0;

// Process()   is invoked when a link has data waiting to be read
//
virtual int           Process(XrdLink *lp) = 0;

// Recycle()   is invoked when this object is no longer needed. The method is
//             passed the number of seconds the protocol was connected to the
//             link and the reason for the disconnection, if any.
//
virtual void          Recycle(XrdLink *lp=0,int consec=0,const char *reason=0)=0;

// Stats()     is invoked when we need statistics about all instances of the
//             protocol. If a buffer is supplied, it must return a null 
//             terminated string in the supplied buffer and the return value
//             is the number of bytes placed in the buffer defined by C99 for 
//             snprintf(). If no buffer is supplied, the method should return
//             the maximum number of characters that could have been returned.
//             Regardless of the buffer value, if do_sync is true, the method
//             should include any local statistics in the global data (if any)
//             prior to performing any action.
//
virtual int           Stats(char *buff, int blen, int do_sync=0) = 0;

            XrdProtocol(const char *jname): XrdJob(jname) {}
virtual    ~XrdProtocol() {}
};

/******************************************************************************/
/*                        X r d g e t P r o t o c o l                         */
/******************************************************************************/
  
/* This extern "C" function must be defined in the shared library plug-in
   implementing your protocol. It is called to obtain an instance of your
   protocol. This allows protocols to live outside of the protocol driver
   (i.e., to be loaded at run-time). The call is made after the call to
   XrdgetProtocolPort() to determine the port to be used (see below) which
   allows e network object (NetTCP) to be proerly defined and it's pointer
   is passed in the XrdProtocol_Config object for your use.

   Required return values:
   Success: Pointer to XrdProtocol object.
   Failure: Null pointer (i.e. 0) which causes the program to exit.

extern "C"  // This is in a comment!
{
       XrdProtocol *XrdgetProtocol(const char *protocol_name, char *parms,
                                   XrdProtocol_Config *pi) {....}
}
*/
  
/******************************************************************************/
/*                    X r d g e t P r o t o c o l P o r t                     */
/******************************************************************************/
  
/* This extern "C" function must be defined for statically linked protocols
   but is optional for protocols defined as a shared library plug-in if the
   rules determining which port number to use is sufficient for your protocol.
   The function is called to obtain the actual port number to be used by the
   the protocol. The default port number is noted in XrdProtocol_Config Port.
   Initially, it has one of the fllowing values:
   <0 -> No port was specified.
   =0 -> An erbitrary port will be assigned.
   >0 -> This port number was specified.

   XrdgetProtoclPort() must return:
   <0 -> Failure is indicated and we terminate
   =0 -> Use an arbitrary port (even if this equals Port)
   >0 -> The returned port number must be used (even if it equals Port)

   When we finally call XrdgetProtocol(), the actual port number is indicated
   in Port and the network object is defined in NetTCP and bound to the port.

   Final Caveats: 1.  The network object (NetTCP) is not defined until
                      XrdgetProtocol() is called.

                  2.  The statistics object (Stats) is not defined until
                      XrdgetProtocol() is called.

                  3.  When the protocol is loaded from a shared library, you need
                      need not define XrdgetProtocolPort() if the standard port
                      determination scheme is sufficient.

extern "C"  // This is in a comment!
{
       int XrdgetProtocolPort(const char *protocol_name, char *parms,
                              XrdProtocol_Config *pi) {....}
}
*/
#endif
