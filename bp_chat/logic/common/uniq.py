# coding: utf-8
import os
import wmi
import binascii
import platform
try:
    import plyer
except ImportError:
    plyer = None
import netifaces as nif
from hashlib import md5

def de(s):
    try:
        return s.decode('utf-8')
    except:
        try:
            return s.decode('cp1251')
        except:
            try:
                return s.decode('cp866')
            except BaseException as e:
                return s

class Uniqizer:

    def all_id(self, sep=None, part=7):
        m = md5()
        try:
            m.update(self.all_id_base())
        except TypeError:
            m.update(self.all_id_base().encode('utf-8'))
        text = m.hexdigest()
        if sep:
            text = sep.join( text[i:i+part] for i in range(0, len(text), part) )
        return text

    def all_id_base(self):
        ids = [de(id) for id in (self.macs_id(), self.drive_id(), self.cpu_id(), self.uuid(), self.pc(), self.user())]
        return (u'-'.join(ids)).replace(u' ',u'')

    def user(self):
        return os.environ.get("USERNAME")

    def pc(self):
        return platform.node()

    def macs_id(self):
        return ';'.join(if_mac for if_mac, if_ip in self.__macs_gen())

    def drive_id(self):
        c = wmi.WMI()
        s = '-'
        for i, x in enumerate(c.Win32_PhysicalMedia()):
            if i == 0 and bool(x.SerialNumber):
                text = x.SerialNumber.strip()
                if len(text) % 2 != 0:
                    text = '0'+text
                try:
                    s = binascii.a2b_hex(text)
                except TypeError:
                    s = x.SerialNumber
                except binascii.Error:
                    s = x.SerialNumber
        return s

    def cpu_id(self):
        return platform.processor()

    def uuid(self):
        if plyer:
            try:
                return plyer.uniqueid.id
            except NotImplementedError:
                pass
            except ImportError:
                pass
            except WindowsError:
                pass
        return ';'.join(platform.win32_ver())

    def __macs_gen(self):
        for i in nif.interfaces():
            addrs = nif.ifaddresses(i)
            try:
                if_mac = addrs[nif.AF_LINK][0]['addr']
                if_ip = addrs[nif.AF_INET][0]['addr']
                yield if_mac, if_ip
            except IndexError:
                pass
            except KeyError:  # ignore ifaces that dont have MAC or IP
                pass

