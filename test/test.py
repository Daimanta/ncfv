#! /usr/bin/env python

import commands,re,os,sys,string,operator,shutil

if hasattr(operator,'gt'):
	op_gt=operator.gt
	op_eq=operator.eq
else:
	def op_gt(a,b): return a>b
	def op_eq(a,b): return a==b


class rcurry:
	def __init__(self, func, *args):
		self.curry_func = func
		self.curry_args = args[:]
	def __call__(self, *_args, **_kwargs):
		return apply(self.curry_func, (_args+self.curry_args), _kwargs)


def pathfind(p, path=string.split(os.environ.get('PATH',os.defpath),os.pathsep)):
	for d in path:
		if os.path.exists(os.path.join(d,p)):
			return 1


class stats:
	ok=0
	failed=0

def logr(text):
	logfile.write(text);
def log(text):
	logr(text+"\n");

def test_log_results(cmd,s,o,r):
	"""
	cmd=command being tested (info only)
	s=return status
	o=output
	r=result (false=ok, anything else=fail (anything other than 1 will be printed))
	"""
	log("*** testing "+cmd);
	log(o);
	if r:
		stats.failed=stats.failed+1
		print "failed test:",cmd
		result="FAILED";
		if type(r)!=type(1) or r!=1:
			result=result+" (%s)"%r
	else:
		stats.ok=stats.ok+1
		result="OK";
	log("%s (%s)"%(result,s));
	log("");
def test_generic(cmd,test):
	s,o=commands.getstatusoutput(cmd)
	r=test(s,o)
	test_log_results(cmd,s,o,r)
class cst_err(Exception): pass
def cfv_stdin_test(cmd,file):
	s1=s2=None
	o1=o2=''
	r=0
	try:
		s1,o1=commands.getstatusoutput(cmd+' '+file)
		if s1: raise cst_err, 2
		s2,o2=commands.getstatusoutput('cat '+file+' | '+cmd+' -')
		if s2: raise cst_err, 3
		x=re.search('^([^\r\n]*)'+re.escape(file)+'(.*)$[\r\n]{0,2}^-: (\d+) files, (\d+) OK.  [\d.]+ seconds, [\d.]+K(/s)?$',o1,re.M|re.DOTALL)
		if not x: raise cst_err, 4
		x2=re.search('^'+re.escape(x.group(1))+'[\t ]*'+re.escape(x.group(2))+'$[\r\n]{0,2}^-: (\d+) files, (\d+) OK.  [\d.]+ seconds, [\d.]+K(/s)?$',o2,re.M)
		if not x2: raise cst_err, 5
	except cst_err, er:
		r=er
	test_log_results('stdin/out of '+cmd+' with file '+file,(s1,s2),o1+'\n'+o2,r)

def rx_test(pat,str):
	if re.search(pat,str): return 0
	return 1
def status_test(s,o):
	if s==0:
		return 0
	return 1

rx_Begin=r'^(?:.* )?(\d+) files, (\d+) OK'
rx_unv=r', (\d+) unverified'
rx_notfound=r', (\d)+ not found'
rx_bad=r', (\d+) bad(crc|size)'
rx_cferror=r', (\d)+ chksum file errors'
rx_End=r'(, \d+ differing cases)?(, \d+ quoted filenames)?.  [\d.]+ seconds, [\d.]+K(/s)?$'
rxo_TestingFrom=re.compile(r'^testing from .* \((.+?)\b.*\)$', re.M)

def tail(s):
	return string.split(s,'\n')[-1]
def cfv_test(s,o, op=op_gt, opval=0):
	x=re.search(rx_Begin+rx_End,tail(o))
	if s==0 and x and x.group(1) == x.group(2) and op(int(x.group(1)),opval):
		return 0
	return 1

def cfv_unv_test(s,o,unv=1):
	x=re.search(rx_Begin+rx_unv+rx_End,tail(o))
	if s!=0 and x and x.group(1) == x.group(2) and int(x.group(1))>0:
		if unv and int(x.group(3))!=unv:
			return 1
		return 0
	return 1

def cfv_unvonly_test(s,o,unv=1):
	x=re.search(rx_Begin+rx_unv+rx_End,tail(o))
	if s!=0 and x and int(x.group(3))==unv:
		return 0
	return 1

def cfv_notfound_test(s,o,unv=1):
	x=re.search(rx_Begin+rx_notfound+rx_End,tail(o))
	if s!=0 and x and int(x.group(2))==0 and int(x.group(1))>0:
		if int(x.group(3))!=unv:
			return 1
		return 0
	return 1

def cfv_cferror_test(s,o,bad=1):
	x=re.search(rx_Begin+rx_cferror+rx_End,tail(o))
	if s!=0 and x and int(x.group(3))>0:
		if bad>0 and int(x.group(3))!=bad:
			return 1
		return 0
	return 1

def cfv_bad_test(s,o,bad=-1):
	x=re.search(rx_Begin+rx_bad+rx_End,tail(o))
	if s!=0 and x and int(x.group(1))>0 and int(x.group(3))>0:
		if bad>0 and int(x.group(3))!=unv:
			return 1
		return 0
	return 1

def cfv_typerestrict_test(s,o,t):
	matches = rxo_TestingFrom.findall(o)
	if not matches:
		return 1
	for match in matches:
		if match != t:
			return 1
	return 0

def cfv_listdata_test(s,o):
	if s==0 and re.search('^data1\0data2\0data3\0data4\0$',o,re.I):
		return 0
	return 1
def joincurpath(f):
	return os.path.join(os.getcwd(), f)
def cfv_listdata_abs_test(s,o):
	if s==0 and re.search('^'+'\0'.join(map(joincurpath, ['data1','data2','data3','data4']))+'\0$',o,re.I):
		return 0
	return 1
def cfv_listdata_unv_test(s,o):
	if os.WEXITSTATUS(s)==32 and re.search('^test.py\0testfix.csv\0$',o,re.I):
		return 0
	return 1
def cfv_listdata_bad_test(s,o):
	if os.WEXITSTATUS(s)&6 and not os.WEXITSTATUS(s)&~6 and re.search('^(d2.)?test4.foo\0test.ext.end\0test2.foo\0test3\0$',o,re.I):
		return 0
	return 1

def cfv_version_test(s,o):
	x=re.search(r'cfv v([\d.]+) -',o)
	x2=re.search(r'cfv ([\d.]+) ',open("../README").readline())
	x3=re.search(r' v([\d.]+):',open("../Changelog").readline())
	if x: log('cfv: '+x.group(1))
	if x2: log('README: '+x2.group(1))
	if x3: log('Changelog: '+x3.group(1))
	if os.path.isdir('../debian'):
		x4=re.search(r'cfv \(([\d.]+)-\d+\) ',open("../debian/changelog").readline())
		if x4: log('deb changelog: '+x4.group(1))
		if not x or not x4 or x4.group(1)!=x.group(1):
			return 1
	if x and x2 and x3 and x.group(1)==x2.group(1) and x.group(1)==x3.group(1):
		return 0
	return 1

def T_test(f):
	test_generic(cfvcmd+" -T -f test"+f,cfv_test)
	test_generic(cfvcmd+" -i -T -f test"+f,cfv_test) #all tests should work with -i
	test_generic(cfvcmd+" -m -T -f test"+f,cfv_test) #all tests should work with -m
	
	test_generic(cfvcmd+" -T --list0=ok -f test"+f+" 2> /dev/null",cfv_listdata_test)
	test_generic(cfvcmd+" -T --showpaths=n-r --list0=ok -f test"+f+" 2> /dev/null",cfv_listdata_test)
	test_generic(cfvcmd+" -T --showpaths=n-a --list0=ok -f test"+f+" 2> /dev/null",cfv_listdata_test)
	test_generic(cfvcmd+" -T --showpaths=a-a --list0=ok -f test"+f+" 2> /dev/null",cfv_listdata_test)
	test_generic(cfvcmd+" -T --showpaths=2-a --list0=ok -f test"+f+" 2> /dev/null",cfv_listdata_test)
	test_generic(cfvcmd+" -T --showpaths=y-r --list0=ok -f test"+f+" 2> /dev/null",cfv_listdata_test)
	test_generic(cfvcmd+" -T --showpaths=y-a --list0=ok -f test"+f+" 2> /dev/null",cfv_listdata_abs_test)
	test_generic(cfvcmd+" -T --showpaths=1-a --list0=ok -f test"+f+" 2> /dev/null",cfv_listdata_abs_test)
	#ensure all verbose stuff goes to stderr:
	test_generic(cfvcmd+" -v -T --list0=ok -f test"+f+" 2> /dev/null",cfv_listdata_test)
	test_generic(cfvcmd+" -v -T --list0=unverified -f test"+f+" test.py testfix.csv data1 2> /dev/null",cfv_listdata_unv_test)

def gzC_test(f,extra=None,verify=None,t=None,d=None):
	cmd=cfvcmd
	if not t:
		t=f
	f2='test.C.'+f+'.tmp.gz'
	f='test.C.'+f+'.gz'
	if extra:
		cmd=cmd+" "+extra
	test_generic("%s -q -C -t %s -zz -f - %s > %s "%(cmd,t,d,f2),status_test)
	test_generic("%s -C -f %s %s"%(cmd,f,d),cfv_test)
	if t in ('sfv', 'sfvmd5', 'crc'):
		#test_generic("zdiff --ignore-matching-lines='^; Generated by .* on .*' %s %s "%(f,f2),status_test) # -I ignores .sfv generated on date ... line
		pass #unfortunatly, zdiff seems to mangle its args or something.. blah.
	else:
		test_generic("zdiff %s %s "%(f,f2),status_test)
	test_generic("%s -T -f %s"%(cmd,f),cfv_test)
	test_generic("cat %s|%s -zz -T -f -"%(f,cmd),cfv_test)
	if verify:
		verify(f)
	os.unlink(f)
	os.unlink(f2)
def C_test(f,extra=None,verify=None,t=None,d='data?'):
	gzC_test(f,extra=extra,t=t,d=d)
	cmd=cfvcmd
	if not t:
		t=f
	cfv_stdin_test(cmd+" -t"+f+" -C -f-","data4")
	f='test.C.'+f
	if extra:
		cmd=cmd+" "+extra
	test_generic("%s -C -f %s %s"%(cmd,f,d),cfv_test)
	test_generic("%s -T -f %s"%(cmd,f),cfv_test)
	test_generic("cat %s|%s -T -f -"%(f,cmd),cfv_test)
	test_generic("gzip -c %s|%s -zz -t%s -T -f -"%(f,cmd,t),cfv_test)
	if verify:
		verify(f)
	os.unlink(f)

	dir='Ce.test'
	try:
		os.mkdir(dir)
		test_generic("%s -p %s -C -f %s"%(cmd,dir,f),rcurry(cfv_test,op_eq,0))
	finally:
		os.rmdir(dir)

def ren_test(f,extra=None,verify=None,t=None):
	join=os.path.join
	dir='n.test'
	dir2=join('n.test','d2')
	basecmd=cfvcmd+' -r -p '+dir
	if extra:
		basecmd=basecmd+" "+extra
	cmd=basecmd+' --renameformat="%(name)s-%(count)i%(ext)s"'
	try:
		os.mkdir(dir)
		os.mkdir(dir2)
		fls=[join(dir,'test.ext.end'),
			join(dir,'test2.foo'),
			join(dir,'test3'),
			join(dir2,'test4.foo')]
		flsf=[join(dir,'test.ext-%i.end'),
			join(dir,'test2-%i.foo'),
			join(dir,'test3-%i'),
			join(dir2,'test4-%i.foo')]
		flsf_1=[join(dir,'test.ext.end-%i'),
			join(dir,'test2.foo-%i'),
			join(dir2,'test4.foo-%i')]
		flsf_2=[join(dir,'test3-%i')]
		def flsw(t,fls=fls):
			for fl in fls:
				open(fl,'wb').write(t)
		def flscmp(t,n,fls=flsf):
			for fl in fls:
				fn= n!=None and fl%n or fl
				try:
					o = open(fn,'rb').read()
					r = o!=t
				except IOError, e:
					r = 1
					o = str(e)
				test_log_results('cmp %s for %s'%(fn,t),r,o,r)
		flsw('hello')
		test_generic("%s -C -t %s"%(cmd,f),cfv_test)
		flsw('1')
		test_generic(basecmd+" --showpaths=0 -v -T --list0=bad 2> /dev/null",cfv_listdata_bad_test)
		test_generic("%s -Tn"%(cmd),cfv_bad_test)
		flsw('11')
		test_generic("%s -Tn"%(cmd),cfv_bad_test)
		flsw('123')
		test_generic("%s -Tn"%(cmd),cfv_bad_test)
		flsw('63')
		test_generic(cmd+' --renameformat="%(fullname)s" -Tn',cfv_bad_test) #test for formats without count too
		flsw('hello')
		test_generic("%s -Tn"%(cmd),cfv_test)
		flscmp('1',0)
		flscmp('11',1)
		flscmp('123',2)
		flscmp('63',1,fls=flsf_1)
		flscmp('63',3,fls=flsf_2)
		flscmp('hello',None,fls=fls)
	finally:
		import glob
		for d in glob.glob(join(dir2,'*')):
			os.unlink(d)
		os.rmdir(dir2)
		for d in glob.glob(join(dir,'*')):
			os.unlink(d)
		os.rmdir(dir)

def symlink_test():
	dir='s.test'
	dir1='d1'
	dir2='d2'
	try:
		os.mkdir(dir)
		os.mkdir(os.path.join(dir, dir1))
		os.mkdir(os.path.join(dir, dir2))
		if hasattr(os, 'symlink'):
			os.symlink(os.path.join(os.pardir, dir2), os.path.join(dir, dir1, 'l2'))
			os.symlink(os.path.join(os.pardir, dir1), os.path.join(dir, dir2, 'l1'))
			test_generic(cfvcmd+" -l -r -p "+dir, rcurry(cfv_test,op_eq,0))
			test_generic(cfvcmd+" -L -r -p "+dir, rcurry(cfv_test,op_eq,0))
			test_generic(cfvcmd+" -l -r -C -p "+dir, rcurry(cfv_test,op_eq,0))
			test_generic(cfvcmd+" -L -r -C -p "+dir, rcurry(cfv_test,op_eq,0))

		open(os.path.join(dir,dir1,'foo'),'w').close()
		open(os.path.join(dir,dir2,'bar'),'w').close()
		def r_unv_test(s,o):
			if cfv_unvonly_test(s,o,2): return 1
			if string.count(o,'not verified')!=1: return 1
			return 0
		test_generic(cfvcmd+" -l -r -u -p "+dir, r_unv_test)
		test_generic(cfvcmd+" -L -r -u -p "+dir, r_unv_test)
		test_generic(cfvcmd+" -l -u -p "+dir, r_unv_test)
		test_generic(cfvcmd+" -L -u -p "+dir, r_unv_test)
		def r_unv_verbose_test(s,o):
			if cfv_unvonly_test(s,o,2): return 1
			if string.count(o,'not verified')!=2: return 1
			return 0
		test_generic(cfvcmd+" -l -uu -p "+dir, r_unv_verbose_test)
		test_generic(cfvcmd+" -L -uu -p "+dir, r_unv_verbose_test)
		test_generic(cfvcmd+" -l -r -uu -p "+dir, r_unv_verbose_test)
		test_generic(cfvcmd+" -L -r -uu -p "+dir, r_unv_verbose_test)
	finally:
		shutil.rmtree(dir)

def deep_unverified_test():
	dir='dunv.test'
	try:
		join = os.path.join
		os.mkdir(dir)
		a = 'a'
		a_C = join(a, 'C')
		B = 'B'
		B_ushallow = join(B,'ushallow')
		B_ushallow_d = join(B_ushallow, 'd')
		u = 'u'
		u_u2 = join(u, 'u2')
		for d in a, a_C, B, B_ushallow, B_ushallow_d, u, u_u2:
			os.mkdir(join(dir,d))
		datafns = ('DATa1', 'UnV1',
				join(a,'dAta2'), join(a, 'Unv2'), join(a_C,'dATa4'), join(a_C,'unV4'),
				join(B,'daTA3'), join(B,'uNv3'),
				join(B_ushallow,'uNvs'), join(B_ushallow_d,'unvP'), join(B_ushallow_d,'datA5'),
				join(u,'uNVu'), join(u,'UnvY'), join(u_u2,'UNVX'),)
		lower_datafns = map(string.lower, datafns)
		for fn in datafns:
			open(join(dir,fn),'w').close()
		f = open(join(dir,'deep.md5'),'w')
		f.write("""d41d8cd98f00b204e9800998ecf8427e *b/DaTa3
d41d8cd98f00b204e9800998ecf8427e *B/ushAllOw/D/daTa5
d41d8cd98f00b204e9800998ecf8427e *a/c/DatA4
d41d8cd98f00b204e9800998ecf8427e *A/dATA2
d41d8cd98f00b204e9800998ecf8427e *daTA1""")
		f.close()
			
		def r_test(s,o):
			if cfv_test(s,o,op_eq,5): return 1
			if string.count(o,'not verified')!=0: return 1
			return 0
		def r_unv_test(s,o):
			if cfv_unvonly_test(s,o,9): return 1
			if string.count(o,'not verified')!=7: return 1
			return 0
		def r_unv_verbose_test(s,o):
			if cfv_unvonly_test(s,o,9): return 1
			if string.count(o,'not verified')!=9: return 1
			return 0
		test_generic(cfvcmd+" -i -U -p "+dir, r_test)
		test_generic(cfvcmd+" -i -u -p "+dir, r_unv_test)
		test_generic(cfvcmd+" -i -uu -p "+dir, r_unv_verbose_test)
		test_generic(cfvcmd+" -i -U -p "+dir+" "+' '.join(lower_datafns), r_test)
		test_generic(cfvcmd+" -i -u -p "+dir+" "+' '.join(lower_datafns), r_unv_verbose_test)
		test_generic(cfvcmd+" -i -uu -p "+dir+" "+' '.join(lower_datafns), r_unv_verbose_test)
	finally:
		shutil.rmtree(dir)
	

cfvcmd='../cfv'

if len(sys.argv)>1:
	if '--help' in sys.argv:
		print 'usage: test.py [cfv]'
		print 'default [cfv] is:',cfvcmd
		sys.exit(1)
	cfvcmd=sys.argv[1]

#set everything to default in case user has different in config file
cfvcmd=cfvcmd+' -ZNVRMUI --fixpaths="" --strippaths=0 --showpaths=auto-relative'


logfile=open("test.log","w")

def all_tests():
	stats.ok = stats.failed = 0

	symlink_test()
	deep_unverified_test()
	
	ren_test('md5')
	ren_test('md5',extra='-rr')
	ren_test('bsdmd5')
	ren_test('sfv')
	ren_test('sfvmd5')
	ren_test('csv')
	ren_test('csv2')
	ren_test('csv4')
	ren_test('crc')

	T_test(".md5")
	T_test(".md5.gz")
	T_test("comments.md5")
	T_test(".bsdmd5")
	#test par spec 1.0 files:
	T_test(".par")
	T_test(".p01")
	#test par spec 0.9 files:
	T_test("v09.par")
	T_test("v09.p01")
	T_test(".par2")
	T_test(".vol0+1.par2")
	T_test(".csv")
	T_test(".sfv")
	T_test("noheader.sfv")
	T_test(".sfvmd5")
	T_test(".csv2")
	T_test(".csv4")
	T_test(".crc")
	T_test("nosize.crc")
	T_test("nodims.crc")
	T_test("nosizenodimsnodesc.crc")
	T_test("crlf.md5")
	T_test("crlf.bsdmd5")
	T_test("crlf.csv")
	T_test("crlf.csv2")
	T_test("crlf.csv4")
	T_test("crlf.sfv")
	T_test("noheadercrlf.sfv")
	T_test("crlf.crc")
	T_test("crcrlf.md5")
	T_test("crcrlf.bsdmd5")
	T_test("crcrlf.csv")
	T_test("crcrlf.csv2")
	T_test("crcrlf.csv4")
	T_test("crcrlf.sfv")
	T_test("noheadercrcrlf.sfv")
	T_test("crcrlf.crc")

	#test handling of directory args in recursive testmode. (Disabled since this isn't implemented, and I'm not sure if it should be.  It would change the meaning of cfv *)
	#test_generic(cfvcmd+" -r a",cfv_test)
	#test_generic(cfvcmd+" -ri a",cfv_test)
	#test_generic(cfvcmd+" -ri A",cfv_test)
	#test_generic(cfvcmd+" -rm a",cfv_test)
	#test_generic(cfvcmd+" -rim a",cfv_test)
	#test_generic(cfvcmd+" -r a/C",cfv_test)
	#test_generic(cfvcmd+" -ri A/c",cfv_test)

	#test handling of testfile args in recursive testmode
	test_generic(cfvcmd+" -r -p a C/foo.bar",cfv_test)
	test_generic(cfvcmd+" -ri -p a c/fOo.BaR",cfv_test)
	test_generic(cfvcmd+" -r -u -p a C/foo.bar",cfv_test)
	test_generic(cfvcmd+" -ri -u -p a c/fOo.BaR",cfv_test)
	
	test_generic(cfvcmd+" --strippaths=0 -T -f teststrip0.csv4",cfv_test)
	test_generic(cfvcmd+" --strippaths=1 -T -f teststrip1.csv4",cfv_test)
	test_generic(cfvcmd+" --strippaths=2 -T -f teststrip2.csv4",cfv_test)
	test_generic(cfvcmd+" --strippaths=all -T -f teststrip-1.csv4",cfv_test)
	test_generic(cfvcmd+" --strippaths=none -T -f teststrip-none.csv4",cfv_notfound_test)

	test_generic(cfvcmd+" -i -T -f testcase.csv",cfv_test)
	test_generic(cfvcmd+" -T -f testquoted.sfv",cfv_test)
	test_generic(cfvcmd+" -i -T -f testquotedcase.sfv",cfv_test)
	test_generic(cfvcmd+" -i -T -f testquoted.csv4",cfv_test)
	test_generic(cfvcmd+r" --fixpaths \\/ -T -f testfix.csv",cfv_test)
	test_generic(cfvcmd+r" --fixpaths \\/ -T -f testfix.csv4",cfv_test)
	test_generic(cfvcmd+r" -i --fixpaths \\/ -T -f testfix.csv4",cfv_test)

	C_test("bsdmd5","-t bsdmd5")#,verify=lambda f: test_generic("md5 -c "+f,status_test)) #bsd md5 seems to have no way to check, only create
	if pathfind('md5sum'): #don't report pointless errors on systems that don't have md5sum
		md5verify=lambda f: test_generic("md5sum -c "+f,status_test)
	else:
		md5verify=None
	C_test("md5",verify=md5verify)
	C_test("csv")
	if pathfind('cksfv'): #don't report pointless errors on systems that don't have cksfv
		sfvverify=lambda f: test_generic("cksfv -f "+f,status_test)
	else:
		sfvverify=None
	C_test("sfv",verify=sfvverify)
	C_test("sfvmd5","-t sfvmd5")
	C_test("csv2","-t csv2")
	C_test("csv4","-t csv4")
	C_test("crc")
	#test_generic("../cfv -V -T -f test.md5",cfv_test)
	#test_generic("../cfv -V -tcsv -T -f test.md5",cfv_test)

	test_generic(cfvcmd+" -m -v -T -t sfv", lambda s,o: cfv_typerestrict_test(s,o,'sfv'))
	test_generic(cfvcmd+" -m -v -T -t sfvmd5", lambda s,o: cfv_typerestrict_test(s,o,'sfvmd5'))
	test_generic(cfvcmd+" -m -v -T -t bsdmd5", lambda s,o: cfv_typerestrict_test(s,o,'bsdmd5'))
	test_generic(cfvcmd+" -m -v -T -t md5", lambda s,o: cfv_typerestrict_test(s,o,'md5'))
	test_generic(cfvcmd+" -m -v -T -t csv", lambda s,o: cfv_typerestrict_test(s,o,'csv'))
	test_generic(cfvcmd+" -m -v -T -t par", lambda s,o: cfv_typerestrict_test(s,o,'par'))
	test_generic(cfvcmd+" -m -v -T -t par2", lambda s,o: cfv_typerestrict_test(s,o,'par2'))

	test_generic(cfvcmd+" -u -t md5 -f test.md5 data* test.py test.md5",cfv_unv_test)
	test_generic(cfvcmd+" -u -f test.md5 data* test.py",cfv_unv_test)
	test_generic(cfvcmd+" -u -f test.md5 data* test.py test.md5",cfv_unv_test)
	test_generic(cfvcmd+r" -i --fixpaths \\/ -Tu",lambda s,o: cfv_unv_test(s,o,None))
	test_generic(cfvcmd+" -T -t md5 -f non_existant_file",cfv_cferror_test)
	test_generic(cfvcmd+" -T -f corrupt/missingfiledesc.par2",cfv_cferror_test)
	test_generic(cfvcmd+" -T -f corrupt/missingmain.par2",cfv_cferror_test)
	test_generic(cfvcmd+" -T -m -f corrupt/missingfiledesc.par2",cfv_cferror_test)
	test_generic(cfvcmd+" -T -m -f corrupt/missingmain.par2",cfv_cferror_test)
	test_generic(cfvcmd+" -h",cfv_version_test)

	donestr="tests finished:  ok: %i  failed: %i"%(stats.ok,stats.failed)
	log("\n"+donestr)
	print donestr

print 'testing...'
all_tests()
s,o=commands.getstatusoutput(cfvcmd+" --version")
if string.find(o,'fchksum')>=0:
	print 'testing without fchksum...'
	cfvcmd="CFV_NOFCHKSUM=x "+cfvcmd
	all_tests()
s,o=commands.getstatusoutput(cfvcmd+" --version")
if string.find(o,'+mmap')>=0:
	print 'testing without mmap...'
	cfvcmd="CFV_NOMMAP=x "+cfvcmd
	all_tests()

