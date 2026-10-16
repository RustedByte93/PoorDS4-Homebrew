#!/usr/bin/env python3
"""Run the actual import collector against bounded, mocked remote memory."""
import os, pathlib, subprocess, tempfile, sys
root = pathlib.Path(__file__).resolve().parents[1]
s = (root / 'payload/wireless_ds4.c').read_text()
def function(name):
    start = s.index('static ', s.index('\n'+name+'(')-20)
    brace = s.index('{', start); depth = 1; end = brace+1
    while depth:
        depth += (s[end] == '{') - (s[end] == '}'); end += 1
    return s[start:end]
types = s[s.index('typedef struct {\n    uint64_t next;'):s.index('static int game_bridge_collect_import_hooks(')]
pre = r'''
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <limits.h>
#include <sys/types.h>
#define __PROSPERO__ 1
#define POORDS4_GAME_BRIDGE_MAX_IMPORT_HOOKS 32
#define R_X86_64_GLOB_DAT 6
#define R_X86_64_JMP_SLOT 7
#define SHN_UNDEF 0
#define STT_FUNC 2
#define STT_NOTYPE 0
#define ELF64_R_TYPE(x) ((uint32_t)(x))
#define ELF64_R_SYM(x) ((x) >> 32)
#define ELF64_ST_TYPE(x) ((x) & 15)
typedef struct { uint64_t r_offset, r_info; int64_t r_addend; } Elf64_Rela;
typedef struct { uint32_t st_name; uint8_t st_info, st_other; uint16_t st_shndx; uint64_t st_value, st_size; } Elf64_Sym;
static struct {uintptr_t p; size_t n;} ranges[16];
static unsigned nr;
static void region(void *p, size_t n) {ranges[nr].p=(uintptr_t)p; ranges[nr++].n=n;}
static int kernel_copyout(intptr_t p, void *out, size_t n) {
 for(unsigned i=0;i<nr;i++) { if((uintptr_t)p>=ranges[i].p && n<=ranges[i].n &&
 (uintptr_t)p-ranges[i].p<=ranges[i].n-n) {memcpy(out,(void*)p,n);return 0;} } return -1;
}
static int game_bridge_process_read(pid_t pid,intptr_t p,void *out,size_t n) {(void)pid;return kernel_copyout(p,out,n);}
static int mdbg_copyout(pid_t pid,intptr_t p,void *out,size_t n) {return game_bridge_process_read(pid,p,out,n);}
static uint8_t proc[0x400], module[1024];
static uint64_t shared;
static intptr_t kernel_get_proc(pid_t pid) {(void)pid;return (intptr_t)proc;}
static int kernel_get_vmem_protection(pid_t pid,intptr_t p,size_t n) {(void)pid;(void)p;(void)n;return 1;}
static int game_bridge_pointer_in_loaded_object(pid_t pid,uint64_t p) {(void)pid;(void)p;return 0;}
static void report_printf(int fd,const char *fmt,...) {(void)fd;(void)fmt;}
static void nid_encode(const char *name,char *out) {
 const char *names[]={"scePadReadState","scePadReadStateExt","scePadRead","scePadReadExt","scePadGetDataInternal","scePadGetControllerInformation","scePadGetExtControllerInformation"};
 for(unsigned i=0;i<7;i++) if(!strcmp(name,names[i])) {snprintf(out,12,"TESTNID%04u",i); return;}
 assert(0);
}
'''
mock = r'''
static void game_bridge_dump_modules_report(pid_t p,intptr_t b,const GameBridgeImportHook *h,uint32_t n) {(void)p;(void)b;(void)h;(void)n;}
'''
post = r'''
static GameBridgeDynlibObjectPrefix object;
static GameBridgeDynlibSectionPrefix section;
static Elf64_Sym syms[2];
static Elf64_Rela rel[2];
static char names[80], path[192];
static intptr_t originals[7]={0x123400,0x123500,0x123600,0x123700,0x123800,0x123900,0x123a00};
static GameBridgeImportHook hooks[32];
static uint32_t count;
static void setup(int plt,const char *name) {
 nr=0;memset(proc,0,sizeof(proc));memset(module,0,sizeof(module));
 memset(&object,0,sizeof(object));memset(&section,0,sizeof(section));
 memset(syms,0,sizeof(syms));memset(rel,0,sizeof(rel));memset(names,0,sizeof(names));
 strcpy(names+1,name);strcpy(path,"/app0/eboot.bin");
 shared=(uintptr_t)&object;uint64_t ptr=(uintptr_t)&shared;memcpy(proc+0x3e8,&ptr,8);
 object.mapbase=(uintptr_t)module;object.mapsize=sizeof(module);object.path=(uintptr_t)path;object.dynsec=(uintptr_t)&section;
 section.symtab=(uintptr_t)syms;section.symtab_size=sizeof(syms);section.strtab=(uintptr_t)names;section.strtab_size=sizeof(names);
 if(plt) {section.plt_rela=(uintptr_t)rel;section.plt_rela_size=sizeof(rel[0]);}
 else {section.rela=(uintptr_t)rel;section.rela_size=sizeof(rel[0]);}
 syms[1].st_name=1;syms[1].st_info=STT_FUNC;
 rel[0].r_offset=64;rel[0].r_info=((uint64_t)1<<32)|(plt?7:6);
 memcpy(module+64,&originals[2],8);
 region(proc,sizeof(proc));region(module,sizeof(module));region(&shared,sizeof(shared));region(&object,sizeof(object));
 region(&section,sizeof(section));region(syms,sizeof(syms));region(rel,sizeof(rel));region(names,sizeof(names));region(path,sizeof(path));
}
static int collect(int allow) {return game_bridge_collect_import_hooks(123,0x777000,originals,hooks,&count,1,allow,0);}
int main(void) {
 setup(0,"scePadRead");assert(collect(0)==0 && count==1 && hooks[0].kind==2);
 setup(0,"scePadReadState");memcpy(module+64,&originals[0],8);assert(collect(0)==0 && hooks[0].kind==0);
 setup(0,"TESTNID0002#A#B");assert(collect(0)==0 && count==1);
 setup(1,"TESTNID0002");assert(collect(0)==0 && count==1);
 setup(0,"scePadReadStateExt");memcpy(module+64,&originals[1],8);assert(collect(0)==0 && hooks[0].kind==1);
 setup(0,"scePadReadBad");assert(collect(0)<0 && count==0);
 setup(0,"TESTNID0002x");assert(collect(0)<0 && count==0);
 setup(0,"scePadRead");rel[0].r_info=((uint64_t)1<<32)|8;assert(collect(0)<0 && count==0);
 setup(0,"scePadRead");rel[0].r_addend=1;assert(collect(0)<0 && count==0);
 setup(0,"scePadRead");syms[1].st_shndx=1;assert(collect(0)<0 && count==0);
 setup(0,"scePadRead");syms[1].st_info=1;assert(collect(0)<0 && count==0);
 setup(0,"scePadRead");rel[0].r_offset=sizeof(module)-4;assert(collect(0)<0 && count==0);
 setup(0,"scePadRead");section.rela_size--;assert(collect(0)<0 && count==0);
 setup(0,"scePadRead");section.rela=0;assert(collect(0)<0 && count==0);
 setup(0,"scePadRead");object.handle=5;strcpy(path,"/system/lib/libScePad.sprx");assert(collect(0)<0 && count==0);
 setup(0,"scePadRead");object.handle=5;strcpy(path,"/app0/fakelib/libScePad.sprx");assert(collect(0)<0 && count==0);
 setup(0,"scePadRead");uint64_t other=0x999000;memcpy(module+64,&other,8);assert(collect(0)<0 && count==0);
 /* The existing stale-recovery caller explicitly requests unexpected slots for validation. */
 assert(collect(1)==0 && count==1);
 setup(0,"scePadRead");section.plt_rela=(uintptr_t)&rel[1];section.plt_rela_size=sizeof(rel[1]);rel[1]=rel[0];rel[1].r_info=((uint64_t)1<<32)|7;
 assert(collect(0)==0 && count==1); /* duplicate across tables */
 setup(0,"scePadRead");section.strtab_size=12;assert(collect(0)==0 && count==1); /* exact boundary */
 setup(0,"scePadRead");section.strtab_size=5;assert(collect(0)<0 && count==0);
 puts("PASS: 21 actual-collector cases (GOT/PLT, identities, bounds, ownership, stale-discovery)");
}
'''
if '--baseline' in sys.argv:
    s = subprocess.check_output(['git', '-C', str(root), 'show',
                                 'HEAD:payload/wireless_ds4.c'], text=True)
    post = post[:post.index('int main(void)')] + r'''int main(void) {
        setup(0,"TESTNID0002");
        assert(collect(0)<0 && count==0);
        puts("PASS: unmodified RC51 collector misses the same GOT-only fixture");
    }'''
with tempfile.TemporaryDirectory(prefix='poords4-scanner-') as tmp:
    c=pathlib.Path(tmp)/'test.c'; exe=pathlib.Path(tmp)/'test'
    c.write_text(pre+types+mock+function('game_bridge_symbol_kind')+'\n'+function('game_bridge_collect_import_hooks')+post)
    subprocess.run([os.environ.get('HOST_CC','clang'),'-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
