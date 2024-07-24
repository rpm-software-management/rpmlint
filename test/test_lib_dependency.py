import pytest
from rpmlint.checks.LibraryDependencyCheck import LibraryDependencyCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package


@pytest.fixture(scope='function', autouse=True)
def libdependencycheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = LibraryDependencyCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [get_tested_mock_package(
files={
'/usr/lib/libfoo.so': {'linkto': 'libfoo.so.1'},
}
)])
def test_shlib2_devel(package, libdependencycheck):
    output, test = libdependencycheck
    test.check(package)
    test.after_checks()
    out = output.print_results(output.results)
    print(out)
    assert 'E: no-library-dependency-for /usr/lib/libfoo.so.1' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
files={
'/usr/bin/xrootd-config',
'/usr/include/xrootd',
'/usr/include/xrootd/XProtocol',
'/usr/include/xrootd/XProtocol/XProtocol.hh',
'/usr/include/xrootd/XProtocol/XPtypes.hh',
'/usr/include/xrootd/Xrd',
'/usr/include/xrootd/Xrd/XrdBuffer.hh',
'/usr/include/xrootd/Xrd/XrdJob.hh',
'/usr/include/xrootd/Xrd/XrdLink.hh',
'/usr/include/xrootd/Xrd/XrdLinkMatch.hh',
'/usr/include/xrootd/Xrd/XrdProtocol.hh',
'/usr/include/xrootd/Xrd/XrdScheduler.hh',
'/usr/include/xrootd/Xrd/XrdTcpMonPin.hh',
'/usr/include/xrootd/XrdCks',
'/usr/include/xrootd/XrdCks/XrdCks.hh',
'/usr/include/xrootd/XrdCks/XrdCksAssist.hh',
'/usr/include/xrootd/XrdCks/XrdCksCalc.hh',
'/usr/include/xrootd/XrdCks/XrdCksData.hh',
'/usr/include/xrootd/XrdCks/XrdCksManager.hh',
'/usr/include/xrootd/XrdCks/XrdCksWrapper.hh',
'/usr/include/xrootd/XrdNet',
'/usr/include/xrootd/XrdNet/XrdNet.hh',
'/usr/include/xrootd/XrdNet/XrdNetAddr.hh',
'/usr/include/xrootd/XrdNet/XrdNetAddrInfo.hh',
'/usr/include/xrootd/XrdNet/XrdNetCmsNotify.hh',
'/usr/include/xrootd/XrdNet/XrdNetConnect.hh',
'/usr/include/xrootd/XrdNet/XrdNetOpts.hh',
'/usr/include/xrootd/XrdNet/XrdNetSockAddr.hh',
'/usr/include/xrootd/XrdNet/XrdNetSocket.hh',
'/usr/include/xrootd/XrdNet/XrdNetUtils.hh',
'/usr/include/xrootd/XrdOuc',
'/usr/include/xrootd/XrdOuc/XrdOucBuffer.hh',
'/usr/include/xrootd/XrdOuc/XrdOucCRC.hh',
'/usr/include/xrootd/XrdOuc/XrdOucCacheCM.hh',
'/usr/include/xrootd/XrdOuc/XrdOucCacheStats.hh',
'/usr/include/xrootd/XrdOuc/XrdOucCallBack.hh',
'/usr/include/xrootd/XrdOuc/XrdOucChain.hh',
'/usr/include/xrootd/XrdOuc/XrdOucCompiler.hh',
'/usr/include/xrootd/XrdOuc/XrdOucDLlist.hh',
'/usr/include/xrootd/XrdOuc/XrdOucEnum.hh',
'/usr/include/xrootd/XrdOuc/XrdOucEnv.hh',
'/usr/include/xrootd/XrdOuc/XrdOucErrInfo.hh',
'/usr/include/xrootd/XrdOuc/XrdOucGMap.hh',
'/usr/include/xrootd/XrdOuc/XrdOucHash.hh',
'/usr/include/xrootd/XrdOuc/XrdOucHash.icc',
'/usr/include/xrootd/XrdOuc/XrdOucIOVec.hh',
'/usr/include/xrootd/XrdOuc/XrdOucLock.hh',
'/usr/include/xrootd/XrdOuc/XrdOucName2Name.hh',
'/usr/include/xrootd/XrdOuc/XrdOucPinObject.hh',
'/usr/include/xrootd/XrdOuc/XrdOucPinPath.hh',
'/usr/include/xrootd/XrdOuc/XrdOucRash.hh',
'/usr/include/xrootd/XrdOuc/XrdOucRash.icc',
'/usr/include/xrootd/XrdOuc/XrdOucSFVec.hh',
'/usr/include/xrootd/XrdOuc/XrdOucStream.hh',
'/usr/include/xrootd/XrdOuc/XrdOucString.hh',
'/usr/include/xrootd/XrdOuc/XrdOucTList.hh',
'/usr/include/xrootd/XrdOuc/XrdOucTable.hh',
'/usr/include/xrootd/XrdOuc/XrdOucTokenizer.hh',
'/usr/include/xrootd/XrdOuc/XrdOucTrace.hh',
'/usr/include/xrootd/XrdOuc/XrdOucUtils.hh',
'/usr/include/xrootd/XrdOuc/XrdOuca2x.hh',
'/usr/include/xrootd/XrdSec',
'/usr/include/xrootd/XrdSec/XrdSecAttr.hh',
'/usr/include/xrootd/XrdSec/XrdSecEntity.hh',
'/usr/include/xrootd/XrdSec/XrdSecEntityAttr.hh',
'/usr/include/xrootd/XrdSec/XrdSecEntityPin.hh',
'/usr/include/xrootd/XrdSec/XrdSecInterface.hh',
'/usr/include/xrootd/XrdSys',
'/usr/include/xrootd/XrdSys/XrdSysAtomics.hh',
'/usr/include/xrootd/XrdSys/XrdSysError.hh',
'/usr/include/xrootd/XrdSys/XrdSysFD.hh',
'/usr/include/xrootd/XrdSys/XrdSysHeaders.hh',
'/usr/include/xrootd/XrdSys/XrdSysLogPI.hh',
'/usr/include/xrootd/XrdSys/XrdSysLogger.hh',
'/usr/include/xrootd/XrdSys/XrdSysPageSize.hh',
'/usr/include/xrootd/XrdSys/XrdSysPlatform.hh',
'/usr/include/xrootd/XrdSys/XrdSysPlugin.hh',
'/usr/include/xrootd/XrdSys/XrdSysPthread.hh',
'/usr/include/xrootd/XrdSys/XrdSysSemWait.hh',
'/usr/include/xrootd/XrdSys/XrdSysTimer.hh',
'/usr/include/xrootd/XrdSys/XrdSysXAttr.hh',
'/usr/include/xrootd/XrdSys/XrdSysXSLock.hh',
'/usr/include/xrootd/XrdVersion.hh',
'/usr/include/xrootd/XrdXml',
'/usr/include/xrootd/XrdXml/XrdXmlReader.hh',
'/usr/lib64/libXrdAppUtils.so',
'/usr/lib64/libXrdCrypto.so',
'/usr/lib64/libXrdCryptoLite.so',
'/usr/lib64/libXrdUtils.so',
'/usr/lib64/libXrdXml.so',
'/usr/share/xrootd',
'/usr/share/xrootd/cmake',
'/usr/share/xrootd/cmake/XRootDConfig.cmake',
}
)])
def test_missing_depency_on(package, libdependencycheck):
    output, test = libdependencycheck
    test.check(package)
    test.after_checks()
    out = output.print_results(output.results)
    assert 'W: missing-dependency-on' not in out
