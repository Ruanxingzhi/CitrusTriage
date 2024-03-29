import re

def get_trace(asan_report):
    a = re.findall(r'CitrusTriage#[\S\s]*?\n', asan_report)
    if not a:
        return ''
    
    out = []

    is_first_block = True

    for x in a:
        p = x.strip()
        if x.startswith('CitrusTriage#0'):
            if is_first_block:
                is_first_block = False
            else:
                break
        
        p = p.split('[', 1)[1]
        p = p.split(']', 1)[0]
        p = p.replace('in ', '')
        p = p.split('(')[0]
        p = p.split('[')[0]

        if not p or p.startswith('_'):
            continue

        out.append(p)

    summary = re.findall(r'SUMMARY: AddressSanitizer: ([\S\s]*?)\n', asan_report)[0]
    summary = summary.split()[0]

    read_or_write = ''

    if 'READ' in asan_report:
        read_or_write = 'READ,'
    if 'WRITE' in asan_report:
        read_or_write = 'WRITE,'

    return f'[{read_or_write}{summary}]@' + '->'.join(out[::-1])

if __name__ == '__main__':
    r = '''=================================================================
==1629955==ERROR: AddressSanitizer: heap-use-after-free on address 0x617000000b00 at pc 0x5555556f1561 bp 0x7fffffffcd30 sp 0x7fffffffc4f8
READ of size 672 at 0x617000000b00 thread T0
CitrusTriage#0 pc=0x5555556f1560 [in __asan_memcpy] at (/work/programs/freeimage/analyze/bin/pure-work.asan+0x19d560) (BuildId: 6cc57296c8d1b785633921754f3c58e27c42e3a4)
CitrusTriage#1 pc=0x5555557337ec [in FreeImage_CreateICCProfile] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/BitmapAccess.cpp:1084:4
CitrusTriage#2 pc=0x555555806696 [in Load(FreeImageIO*, void*, int, int, void*)] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/PluginTIFF.cpp:2324:3
CitrusTriage#3 pc=0x55555574d258 [in FreeImage_LoadFromHandle] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/Plugin.cpp:386:24
CitrusTriage#4 pc=0x55555574d40a [in FreeImage_Load] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/Plugin.cpp:406:22
CitrusTriage#5 pc=0x55555573034a [in main] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/fuzz/work.cpp:9:25
CitrusTriage#6 pc=0x7ffff7a456c9 [] at (/lib/x86_64-linux-gnu/libc.so.6+0x276c9) (BuildId: 8a1bf172e710f8ca0c1576912c057b45f90d90d8)
CitrusTriage#7 pc=0x7ffff7a45784 [in __libc_start_main] at (/lib/x86_64-linux-gnu/libc.so.6+0x27784) (BuildId: 8a1bf172e710f8ca0c1576912c057b45f90d90d8)
CitrusTriage#8 pc=0x5555556576e0 [in _start] at (/work/programs/freeimage/analyze/bin/pure-work.asan+0x1036e0) (BuildId: 6cc57296c8d1b785633921754f3c58e27c42e3a4)

0x617000000b00 is located 0 bytes inside of 672-byte region [0x617000000b00,0x617000000da0)
freed by thread T0 here:
CitrusTriage#0 pc=0x5555556f208a [in __interceptor_free] at (/work/programs/freeimage/analyze/bin/pure-work.asan+0x19e08a) (BuildId: 6cc57296c8d1b785633921754f3c58e27c42e3a4)
CitrusTriage#1 pc=0x5555557fcf14 [in _TIFFfree] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/PluginTIFF.cpp:229:2
CitrusTriage#2 pc=0x555555a846e8 [in _TIFFfreeExt] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_open.c:165:5
CitrusTriage#3 pc=0x5555559d4b44 [in TIFFFreeDirectory] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_dir.c:1647:13
CitrusTriage#4 pc=0x555555a1a4d3 [in TIFFReadCustomDirectory] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_dirread.c:5124:5
CitrusTriage#5 pc=0x555555a1c3d9 [in TIFFReadEXIFDirectory] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_dirread.c:5238:12
CitrusTriage#6 pc=0x55555580adb7 [in tiff_read_exif_profile(FreeImageIO*, void*, tiff*, FIBITMAP*)] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/PluginTIFF.cpp:852:7
CitrusTriage#7 pc=0x555555809653 [in ReadMetadata(FreeImageIO*, void*, tiff*, FIBITMAP*)] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/PluginTIFF.cpp:880:2
CitrusTriage#8 pc=0x5555558065fa [in Load(FreeImageIO*, void*, int, int, void*)] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/PluginTIFF.cpp:2320:3
CitrusTriage#9 pc=0x55555574d258 [in FreeImage_LoadFromHandle] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/Plugin.cpp:386:24
CitrusTriage#10 pc=0x55555574d40a [in FreeImage_Load] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/Plugin.cpp:406:22
CitrusTriage#11 pc=0x55555573034a [in main] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/fuzz/work.cpp:9:25
CitrusTriage#12 pc=0x7ffff7a456c9 [] at (/lib/x86_64-linux-gnu/libc.so.6+0x276c9) (BuildId: 8a1bf172e710f8ca0c1576912c057b45f90d90d8)

previously allocated by thread T0 here:
CitrusTriage#0 pc=0x5555556f2769 [in __interceptor_realloc] at (/work/programs/freeimage/analyze/bin/pure-work.asan+0x19e769) (BuildId: 6cc57296c8d1b785633921754f3c58e27c42e3a4)
CitrusTriage#1 pc=0x5555557fcf3c [in _TIFFrealloc] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/PluginTIFF.cpp:234:9
CitrusTriage#2 pc=0x555555a846b3 [in _TIFFreallocExt] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_open.c:158:12
CitrusTriage#3 pc=0x5555559cb678 [in _TIFFCheckRealloc] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_aux.c:107:14
CitrusTriage#4 pc=0x5555559cb720 [in _TIFFCheckMalloc] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_aux.c:125:12
CitrusTriage#5 pc=0x5555559e1c9b [in _TIFFVSetField] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_dir.c:819:29
CitrusTriage#6 pc=0x5555559d3223 [in TIFFVSetField] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_dir.c:1208:18
CitrusTriage#7 pc=0x5555559d312e [in TIFFSetField] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_dir.c:1152:14
CitrusTriage#8 pc=0x555555a0fb2f [in TIFFFetchNormalTag] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_dirread.c:6926:21
CitrusTriage#9 pc=0x5555559ff384 [in TIFFReadDirectory] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_dirread.c:4617:27
CitrusTriage#10 pc=0x555555a87a19 [in TIFFClientOpenExt] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_open.c:629:17
CitrusTriage#11 pc=0x555555a8476e [in TIFFClientOpen] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/LibTIFF4/tif_open.c:174:12
CitrusTriage#12 pc=0x5555557fc529 [in TIFFFdOpen(void*, char const*, char const*)] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/PluginTIFF.cpp:193:14
CitrusTriage#13 pc=0x5555557fd4fc [in Open(FreeImageIO*, void*, int)] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/PluginTIFF.cpp:1096:14
CitrusTriage#14 pc=0x55555574d016 [in FreeImage_Open] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/Plugin.cpp:360:15
CitrusTriage#15 pc=0x55555574d1e8 [in FreeImage_LoadFromHandle] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/Plugin.cpp:384:18
CitrusTriage#16 pc=0x55555574d40a [in FreeImage_Load] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/Source/FreeImage/Plugin.cpp:406:22
CitrusTriage#17 pc=0x55555573034a [in main] at /work/programs/freeimage/freeimage-svn/FreeImage/trunk/fuzz/work.cpp:9:25
CitrusTriage#18 pc=0x7ffff7a456c9 [] at (/lib/x86_64-linux-gnu/libc.so.6+0x276c9) (BuildId: 8a1bf172e710f8ca0c1576912c057b45f90d90d8)

SUMMARY: AddressSanitizer: heap-use-after-free (/work/programs/freeimage/analyze/bin/pure-work.asan+0x19d560) (BuildId: 6cc57296c8d1b785633921754f3c58e27c42e3a4) in __asan_memcpy
Shadow bytes around the buggy address:
0x617000000880: fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd
0x617000000900: fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd
0x617000000980: fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd
0x617000000a00: fd fd fd fd fa fa fa fa fa fa fa fa fa fa fa fa
0x617000000a80: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
=>0x617000000b00:[fd]fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd
0x617000000b80: fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd
0x617000000c00: fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd
0x617000000c80: fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd
0x617000000d00: fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd
0x617000000d80: fd fd fd fd fa fa fa fa fa fa fa fa fa fa fa fa
Shadow byte legend (one shadow byte represents 8 application bytes):
Addressable: 00
Partially addressable: 01 02 03 04 05 06 07
Heap left redzone: fa
Freed heap region: fd
Stack left redzone: f1
Stack mid redzone: f2
Stack right redzone: f3
Stack after return: f5
Stack use after scope: f8
Global redzone: f9
Global init order: f6
Poisoned by user: f7
Container overflow: fc
Array cookie: ac
Intra object redzone: bb
ASan internal: fe
Left alloca redzone: ca
Right alloca redzone: cb
==1629955==ABORTING'''
    print(get_trace(r))
