# Free to use and distribute with credit to github.com/alm999 
#
# A simple, but customizable, script to manage configuration files
# By default, configuration files consist on sections and key/values in those sections, as below
# [Section1]
# key1 = value1
# # A comment
# key2 = value2
#
# [Section2]
# key1 = value1
# key2 = value2
#
# They can also have a special section ('CONFIG_ARGS' by default) which stores variables
# [CONFIG_ARGS]
# variable1 = something
# variable2 = something
#
# [Section1]
# key1 = %variable1%
# key2 = value2
#
# [Section2]
# key1 = value1
# key2 = value2
#
#
# All customizations are done on the object instantiation, which by default only takes the filename as argument
# To customize the symbols of the file, more arguments can be passed on creation: assignment_symbol, comment_symbol
# Arrays of length 2 for identifying sections and variables can also be passed as arguments: section_symbols and variable_symbols
# The keyword for variable sections can be customized by passing: variable_section
# By passing a 'section' argument during instantiation, only variables from that section of the file can be read/edited (only with dict=False)
#
# Data in the object can be accessed and edited in two ways:
# 1. Via functions. Simpler mode. These operate directly on the data files, so if update() is called, it will immediately update the file.
# 2. Via dictionary mode. Experimental mode. These operate on the stored data in the runtime and won't modify the file unless save() is called.
#
# Dictionary mode has to be manually enabled by setting dict=True on instantiation. Alpha feature
# Worth noting that save() will only overwrite the file contents that have been edited. (Only with dict=True)
# Sections can be created and deleted entirely (only in dict mode)

# Note: function mode is more limited but stabler. Ideally both will end up with the same reliability and abilities.

# Dict save function not available. Save must determine the variables

"""
    Script class ConfigManager
    Mandatory parameter:
        file: the file from where the config will be read
    Optional parameters:
        section: the section to edit from the config file. Defaults to all
        dict: allow dictionary-type access. Defaults to True. If false, provided functions will need to be used to access and edit the config file.
        assignment_symbol, comment_symbol, section_symbols, variable_symbols: the symbols to use to identify the line. Defaults to =, #, [ and ["%", "%"]
        variable_section: the name of the section where the variables of the file will be stored. Default is CONFIG_VARS (case sensitive)
"""
class ConfigManager:
    def __init__(self, file, dict=False, section="", assignment_symbol="=", comment_symbol="#", section_symbols=["[", "]"], variable_symbols=["%", "%"], variable_section="CONFIG_ARGS"):
        self.file = file
        self.__data = {} # holds sections
        self.__variables = {} # holds file variables
        self.__dict = dict
        self.section = section
        self.assignment_symbol = assignment_symbol
        self.comment_symbol = comment_symbol
        self.section_symbols = section_symbols
        self.variable_symbols = variable_symbols
        self.variable_section = variable_section

        if self.__dict == True:
            self.__data, self.__variables = self.__load_file()


    # Get a value from the config file
    def get(self, *args):
        if len(args) == 1:
            if self.section == "":
                raise TypeError("get() missing 1 required positional argument: 'section'")
            return self.line_operation("get", section=self.section, key=args[0])
        elif len(args) == 2:
            return self.line_operation("get", section=args[0], key=args[1])
        else:
            if self.section == "":
                raise TypeError("get() missing 2 required positional arguments: 'section', 'key'")
            raise TypeError("get() missing 1 required positional argument: 'section'")

    # Update a value from the config file
    def update(self, *args):
        if len(args) == 2:
            if self.section == "":
                raise TypeError("Usage update('section', 'key', 'value')")
            return self.line_operation("update", self.section, args[0], args[1])
        elif len(args) == 3:
            return self.line_operation("update", args[0], args[1], args[2])
        else:
            if self.section == "":
                raise TypeError("Usage update('section', 'key', 'value')")
            raise TypeError("Usage update('key', 'value')")

    # Delete a key=value pair from the config file
    def delete(self, *args):
        if len(args) == 1:
            if self.section == "":
                raise TypeError("delete() missing 1 required positional argument: 'section'")
            return self.line_operation("delete", section=self.section, key=args[0])
        elif len(args) == 2:
            return self.line_operation("delete", section=args[0], key=args[1])
        else:
            if self.section == "":
                raise TypeError("delete() missing 2 required positional arguments: 'section', 'key'")
            raise TypeError("delete() missing 1 required positional argument: 'section'")

    # Create a key=value pair
    def new(self, *args):
        if len(args) == 2:
            if self.section == "":
                raise TypeError("Usage new('section', 'key', 'value')")
            return self.line_operation("new", self.section, args[0], args[1])
        elif len(args) == 3:
            return self.line_operation("new", args[0], args[1], args[2])
        else:
            if self.section == "":
                raise TypeError("Usage new('section', 'key', 'value')")
            raise TypeError("Usage new('key', 'value')")

    # Read file and perform operations on values
    def line_operation(self, operation, section, key, new_value=""):
        if self.section != "" and self.section != section:
            raise Exception("Cannot operate on a different section than " + self.section)
        with open(self.file) as f:
            lines = f.read().splitlines()

        current_section = ""
        key_error = True
        the_line = -1
        variables = {}

        for i in range(0, len(lines)):
            if len(lines[i]) == 0 or lines[i][0] == self.comment_symbol: # Ignore empty lines
                continue
            elif lines[i][0] == self.section_symbols[0] and lines[i][-1] == self.section_symbols[1]: # Update actual section
                new_section_name = lines[i][1:-1]
                # Before coming into new section, create a new key=value for current section
                if operation == "new" and current_section == section:
                    the_line = i
                    break
                # New section
                current_section = lines[i][1:-1]
            elif current_section == self.variable_section: # Store variables
                key_value = self.__obtain_key_value(lines[i])
                variables[key_value[0]] = key_value[1]
            else: # Do operations on key=value line
                if section != current_section:
                    continue

                key_value = self.__obtain_key_value(lines[i])

                # Check key
                if key_value[0] == key:
                    the_line = i
                    key_error = False
                    break

        if key_error == True and operation != "new":
            raise KeyError(key)

        # Operations
        if the_line == -1:
            return
        elif operation == "new":
            if key_error == False:
                raise Exception("Key exists")
            lines = lines[0:the_line-1] + [key + " " + self.assignment_symbol + " " + new_value] + lines[the_line-1:]
        elif operation == "update":
            key_value = self.__obtain_key_value(lines[the_line])
            lines[the_line] = key_value[0] + " " + self.assignment_symbol + " " + new_value
        elif operation == "get":
            return self.replace_variables(self.__obtain_key_value(lines[the_line])[1], variables)
        elif operation == "delete":
            del(lines[the_line])

        with open(self.file, "w") as f:
            for i in range(0, len(lines)):
                lines[i] = lines[i] + "\n"
            f.writelines(lines)

    def __obtain_key_value(self, line):
        key_value = line.split(self.assignment_symbol)
        # Remove escape symbol from key
        # if key_value[0] == self.escape_symbol:
        #     key_value[0] = key_value[0][1:]
        # Remove spaces between assignment symbol
        if key_value[0][-1:] == " ":
            key_value[0] = key_value[0][:-1]
        if key_value[1][:1] == " ":
            key_value[1] = key_value[1][1:]
        return [key_value[0], key_value[1]]

    def replace_variables(self, line, vars):
        if self.variable_symbols[0] not in line and self.variable_symbols[1] not in line:
            return line

        # Account for all variable possibilities
        try:
            i = line.index(self.variable_symbols[0])
            j = line.index(self.variable_symbols[1], i+1)
        except ValueError: # Exist but in wrong order if they are different
            return line
        while line.count(self.variable_symbols[0], i) > 0:
            while line.count(self.variable_symbols[1], j) > 0:
                # If occurance, update line
                if line[i+1:j] in vars:
                    line = line[:i] + vars[line[i+1:j]] + line[j+1:]
                try: # Update second var symbol. If not found, break to update both and start again
                    j=line.index(self.variable_symbols[1], j+1)
                except ValueError:
                    break
            try: # Update first var symbol and reset second. If no more combinations available
                i = line.index(self.variable_symbols[0], i+1)
                j = line.index(self.variable_symbols[1], i+1)
            except ValueError:
                break

        return line


    ###########################
    # Functions for DICT MODE #
    ###########################

    # Classes for dict simulation

    class __SectionStructure:
        def __init__(self, configmanager, name, operation="", children={}):
            self.name = name
            self.operation = operation
            self.__children = children
            self.__list = []
            self.__configmanager = configmanager # Access parent methods

        def __str__(self):
            a = []
            for section in self.__children.keys():
                if not self.__children[section].pending_deletion():
                    a.append(section)
            return str(a)
        def __getitem__(self, key):
            return self.__children[key]
        def __setitem__(self, key, value):
            if key not in self.__children:
                self.__children[key] = self.KeyValueStructure(self.__configmanager, key, value, operation="new")
            else:
                self.__children[key][""] = value # update
        def __delitem__(self, key):
            self.__children[key].operation = "delete"

        def __iter__(self):
            self.list = list(self.__children.keys())
            return self
        def __next__(self):
            try:
                return self.list.pop()
            except IndexError:
                raise StopIteration

        def keys(self):
            return self.__children.keys()
        def pending_deletion(self): # Clearer code
            return self.operation == "delete"
        class KeyValueStructure:
            def __init__(self, configmanager, key, value, operation=""):
                self.__key = key
                self.__value = value
                self.__configmanager = configmanager # Access parent methods
                self.operation = operation

            def __str__(self):
                return self.__configmanager.replace_variables(self.__value, self.__configmanager.vars())
            def __getitem__(self, key):
                return self.__configmanager.replace_variables(self.__value, self.__configmanager.vars())
            def __setitem__(self, key, value):
                self.operation = "update"
                self.__value = value
            def __delitem__(self, key):
                self.operation = "delete"

            def pending_deletion(self): # Clearer code
                return self.operation == "delete"

    # Uncommon functions (dict simulation)

    def __str__(self):
        a = []
        for section in self.__data.keys():
            if not self.__data[section].pending_deletion():
                a.append(section)
        return str(a)
    def __getitem__(self, key):
        return self.__data[key]
    def __setitem__(self, key, value):
        if key in self.__data.keys():
            if not self.__data[key].pending_deletion():
                raise Exception("Cannot assign value to existing section. Please manually delete it first")
            else:
                raise Exception("Cannot assign value to section pending deletion. Please save changes first")
        self.__data[key] = self.__SectionStructure(self, key, operation="new")
    def __delitem__(self, key):
        self.__data[key].operation = "delete"

    def keys(self):
        return self.__data.keys()
    def vars(self):
        return self.__variables

    def data(self): # Debug
        return self.__data

    # Common functions (for intended functionality)

    def dict_enforce(self):
        if self.__dict == False:
            raise Exception("This feature is only available when using dict")

    # Returns a dictionary of the object file
    def __load_file(self):
        data = {}
        variables = {}
        # Read file
        with open(self.file) as f:
            lines = f.read().splitlines()
        # Write into data dictionary
        current_section = ""
        section_children = {}
        for line in lines:
            # Ignore blank lines and comments in file
            if len(line) == 0 or line[0] == self.comment_symbol:
                continue
            # Check if line is a section
        elif line[0] == self.section_symbols[0] and line[-1] == self.section_symbols[1]:
                # Save previous section
                if current_section != "" and current_section != self.variable_section:
                    data[section_name] = self.__SectionStructure(self, section_name, children=section_children)
                    section_children = {}
                # Validate new section
                section_name = line[1:-1]
                if self.section != "" and self.section != section_name:
                    current_section = ""
                else:
                    current_section = section_name
            # Variable section, so line is variable Key = value
            elif current_section == self.variable_section: # Store variables
                key_value = self.__obtain_key_value(line)
                variables[key_value[0]] = key_value[1]
            # Line is Key = value
            else:
                if current_section == "": # Section not valid
                    continue
                key_value = self.__obtain_key_value(line)
                # Check if key value is from valid section and store as ConfigValue object
                section_children[key_value[0]] = self.__SectionStructure.KeyValueStructure(self, key_value[0], key_value[1])

        if current_section != "": # Save last section
            data[section_name] = self.__SectionStructure(self, section_name, children=section_children)
        return data, variables

    # Save edited values to the config file.
    def save(self):
        return
        self.dict_enforce()
        # Check what has been altered
        for section in list(self.__data):
            for key_value in self.__data[section]:
                if self.__data[section][key_value].operation == "":
                    print(key_value, self.__data[section][key_value].operation)
                    del(self.__data[section][key_value])
            if len(list(self.__data[section])) == 0:
                del(self.__data[section])

        # Read file
        # Edit file by checking if something has been altered
        # Check news
        # Write file
        # self.__data = self.__load_file()
        pass
