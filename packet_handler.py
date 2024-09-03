from DataTypes import *

def edit_book(str):
    #Slot info
    is_present, bytearr = Boolean().unpack(bytearray(str))
    if not is_present:
        return
    item_id, bytearr = VarInt().unpack(bytearr)
    item_count, bytearr = VarInt().unpack(bytearr)
    print(f"Present: {is_present}, ID: {item_id}, Count: {item_count}")