import pint as pi
ureg = pi.UnitRegistry()
import re

class Ingredient():
    def __init__(self, name, allnames=None, density=None, units_handler=None):
        self.name = name
        if allnames is None:
            self.allnames = set([name])
        else:
            self.allnames = set(allnames)
        self.density = density # SI base units [kg/L]
        self.uh = units_handler
            
    def match_string(self, string):
        for n in self.allnames:
            if re.search(n,string) is not None:
                return True
        return False
    
    def convert(self, magnitude, from_unit, to_unit=None):
        if to_unit is None:
            to_unit = 'liter'
        v1 = self.uh.volume.match_unit(from_unit)
        m1 = self.uh.mass.match_unit(from_unit)
        v2 = self.uh.volume.match_unit(to_unit)
        m2 = self.uh.mass.match_unit(to_unit)
        if ((v1 is None) and (m1 is None)):
            raise ValueError("couldn't find the from_unit")
        if ((v2 is None) and (m2 is None)):
            raise ValueError("couldn't find the to_unit")
        if ((v1 is not None) and (m1 is not None)):
            raise ValueError("ambiguity in from_unit")
        if ((v2 is not None) and (m2 is not None)):
            raise ValueError("ambiguity in to_unit")
        if v1 is None:
            newmag = m1.convert_to_SI(magnitude)
            if v2 is None:
                return m2.convert_from_SI(newmag), to_unit
            else:
                if self.density is None:
                    raise ValueError('density not specified, cannot convert')
                return v2.convert_from_SI(newmag/self.density), to_unit
        else:
            newmag = v1.convert_to_SI(magnitude)
            if v2 is None:
                if self.density is None:
                    raise ValueError('density not specified, cannot convert')
                return m2.convert_from_SI(newmag*self.density), to_unit
            else:
                return v2.convert_from_SI(newmag), to_unit

            
class IngredientsHandler():
    def __init__(self, units_handler):
        self.uh = units_handler
        self.ingredients = []
        self.add_ingredient('flour',0.55)
        self.add_ingredient('salt',1.2)
        self.add_ingredient('sugar',0.8)
        self.add_ingredient('water',1.)
        self.add_ingredient('butter',0.9)
        self.add_ingredient('vanilla')

    def add_ingredient(self, name, density=None):
        self.ingredients.append(Ingredient(name, density=density, units_handler=self.uh))
    
    def match_name(self, name):
        for i in self.ingredients:
            if i.match_string(name):
                return i

    def convert(self, name, magnitude, from_unit, to_unit):
        i = self.match_name(name)
        if i is None:
            raise ValueError("can't match ingredient name")
        return i.convert(magnitude, from_unit, to_unit)

class UnitSet():
    '''class to control a set of convertable units'''
    def __init__(self, name, SI_unit):
        self.name = name
        self.SI_unit = SI_unit
        self.units = []
        
    def match_unit(self, string):
        '''matches the given string to a unit contained within the class'''
        for u in self.units:
            if u.match(string):
                return u
        return None
    
    def convert(self, magnitude, unit_name, to_unit=None):
        u = self.match_unit(unit_name)
        if u is None:
            raise ValueError("can't match the present unit given")
        else:
            newmag = u.convert_to_SI(magnitude)
            if to_unit is None:
                return newmag, self.SI_unit
            else:
                to_u = self.match_unit(to_unit)
                if to_u is not None:
                    return to_u.convert_from_SI(newmag), to_unit
                else:
                    raise ValueError("can't match the present unit given")
        
class Unit():
    '''class to define a particular unit (cup, kg, pinch, etc.), it's names, and it's conversion to SI'''
    def __init__(self, name, SI_unit, allnames=None, SI_ratio=None, SI_offset=0., case_sensitive=False):
        self._SI_units = {'meter','kilogram','second','liter','kelvin','unknown'}
        self.name = name
        if SI_ratio is None:
            self.SI_ratio = ureg.parse_expression(name.replace(' ','_')).to(SI_unit).magnitude
        else:
            self.SI_ratio = SI_ratio
        self.SI_offset = SI_offset
        if SI_unit in self._SI_units:
            self.SI_unit = SI_unit
        else:
            raise ValueError('SI_name given is not valid')
        
        if allnames is None:
            self.allnames = set([name])
        else:
            self.allnames = set(allnames)
        self.case_sensitive = case_sensitive

    def expand_allnames(self):
        '''list all valid names for the unit'''
        pn = list(self.allnames)
        for p in pn:
            self.allnames.add(p+'.')
            self.allnames.add(p+'s')
            self.allnames.add(p+'s.')

    def match(self, string, case_sensitive=None):
        '''match a given string to this unit name. 

        returns True if the string matches this unit name, False otherwise'''
        if case_sensitive is None:
            case_sensitive = self.case_sensitive
        if case_sensitive:
            for n in self.allnames:
                if re.match(n+'s?\.?($|\b)', string):
                    return True
        else:
            for n in self.allnames:
                if re.match(n+'s?\.?($|\b)', string, re.IGNORECASE):
                    return True            
        return False

    def convert_to_SI(self, magnitude):
        ''' converts this unit to the SI base unit'''
        return magnitude*self.SI_ratio + self.SI_offset
    
    def convert_from_SI(self, magnitude):
        return (magnitude-self.SI_offset)/self.SI_ratio

class UnitsHandler():
    def __init__(self):
        # units of volume
        volume = UnitSet('volume','liter')
        volume.units.append(Unit('liter','liter', allnames=['liter','litre','l','litr','ltr']))
        volume.units.append(Unit('deciliter','liter', allnames=['deciliter','decilitre','dl']))
        volume.units.append(Unit('milliliter','liter', allnames=['milliliter','millilitre','ml','cc',]))
        
        volume.units.append(Unit('drop','liter', allnames=['drop','d','dr','gt','gtt'], SI_ratio=0.050e-3))
        volume.units.append(Unit('smidgen','liter', allnames=['smidgen','smidge','smidg','smdgn','smdg','smi'], SI_ratio=0.116e-3))
        volume.units.append(Unit('pinch','liter', allnames=['pinch',], SI_ratio=0.231e-3))
        volume.units.append(Unit('dash','liter', allnames=['dash','dsh'], SI_ratio=0.462e-3))
        volume.units.append(Unit('saltspoon','liter', allnames=['saltspoon','scruple','ssp'], SI_ratio=0.924e-3))
        volume.units.append(Unit('coffeespoon','liter', allnames=['coffeespoon','csp','cfespn'], SI_ratio=0.924e-3))
        volume.units.append(Unit('fluid dram','liter', allnames=['fluid dram','fl.dr','fl. dr','fldr','fl dr'], SI_ratio=0.924e-3))
        volume.units.append(Unit('teaspoon','liter', allnames=['teaspoon','Teaspoon', 't','tsp','ts'], case_sensitive=True))
        volume.units.append(Unit('dessertspoon','liter', allnames=['dessertspoon','dsp','dstspn','dssp','dsspn','dspn'], SI_ratio=0.01))
        volume.units.append(Unit('tablespoon','liter', allnames=['tablespoon','Tablespoon','tbl','tblspn','tbspn','tb','tbs','tbsp','T','TB','Tbsp','Tblsp','Tbl','Tbs','TBsp','TBl'], case_sensitive=True))
        volume.units.append(Unit('fluid ounce','liter', allnames=['fluid ounce','ounce','fl oz','floz','fl. oz', 'oz']))
        volume.units.append(Unit('wineglass','liter', allnames=['wineglass','wine glass','wgf','wg','winegl','wngl'], SI_ratio=59.15e-3))
        volume.units.append(Unit('teacup','liter', allnames=['teacup','gill','tcf','tc','teac'], SI_ratio=0.1189))
        volume.units.append(Unit('cup','liter', allnames=['cup','c','cu']))
        volume.units.append(Unit('pint','liter', allnames=['pint','pnt','p','pt','flpt','fl pt','fl. pt','fl.pt']))
        volume.units.append(Unit('quart','liter', allnames=['quart','quarts','q','qt','fl qt','fl. qt','fl.qt',]))
        volume.units.append(Unit('pottle','liter', allnames=['pottle','ptl',], SI_ratio=1.892))
        volume.units.append(Unit('gallon','liter', allnames=['gallon','g','ga','gal','gall']))
        # misc units that I need to handle TODO
        package = Unit('package','liter', allnames=['package',], SI_ratio=-1, SI_offset=-1)
        bag = Unit('bag','liter', allnames=['bag',], SI_ratio=-1, SI_offset=-1)
        can = Unit('can','liter', allnames=['can','cn',], SI_ratio=-1, SI_offset=-1)

        # units of mass
        mass = UnitSet('mass','kilogram')
        mass.units.append(Unit('kilogram','kilogram', allnames=['kilogram','kg','kgr','kigr']))
        mass.units.append(Unit('gram','kilogram', allnames=['gram','g','gr']))
        mass.units.append(Unit('pound','kilogram', allnames=['pound','lb','lbs',]))

        # units of temperature
        temperature = UnitSet('temperature','kelvin')
        temperature.units.append(Unit('fahrenheit','kelvin',allnames=['F','degF','deg F'], SI_offset=255.372, SI_ratio=5/9))
        temperature.units.append(Unit('celsius','kelvin',allnames=['C','degC','deg C'], SI_offset=273.15, SI_ratio=1))
        temperature.units.append(Unit('kelvin','kelvin',allnames=['C','degC','deg C'], SI_offset=1, SI_ratio=1))


        self.volume = volume
        self.mass = mass
        self.temperature = temperature
