import telebot
import sqlite3  #1 of 1 ivan contribution
import copy

global temp_order_data
temp_order_data = []
global myOrders
myOrders = []
global myDeliveries
myDeliveries = []

connection = sqlite3.connect('orders.db', check_same_thread=False)
mcurs = connection.cursor()
#mcurs.execute("DROP TABLE orders")
mcurs.execute(
    """CREATE TABLE IF NOT EXISTS orders (orderID INTEGER PRIMARY KEY, Location VARCHAR(45) NOT NULL, Destination VARCHAR(45) NOT NULL, Recipient VARCHAR(45) NOT NULL, Deliverer VARCHAR(45), Status VARCHAR(45), Food VARCHAR(45), dID VARCHAR(45), rID VARCHAR(45))"""
)
connection.commit()

bot = telebot.TeleBot("6342599183:AAG5ppGT0PnvhnIzTyCAtGnqx_RMQwZ0hGo")


#reply to start and hello
def format_text(number, array):
  text = [
      'orderID', 'Location', 'Destination', 'Recipient', 'Deliverer', 'Status',
      'Food'
  ]
  output = 'Number: ' + str(number) + '\n'
  for i in range(len(array) - 2):
    item = ''
    if (array[i] == None):
      item = 'null'
    else:
      item = array[i]
    output += text[i] + ': ' + str(item) + '\n'
  return output


def ignore_case(string1, string2):
  return string1.lower() == string2.lower()


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
  #bot.reply_to(message, "Hi! My favourite k-drama is CLOY. What's yours? ;)")
  # await message.reply("Hello! how are you?", reply_markup=keyboard_reply)
  bot.reply_to(
      message,
      "Hi! Welcome to NUS_Goon_Bot. Available commands: \n1. /order \n2. /deliver \n3. /checkOrder \n4. /updateStatus"
  )


#Option 1 Branch: Ordering

#Option 2 Branch: Delivering


#Option 3 Branch: Checking Orders
@bot.message_handler(commands=['checkOrder'])
def check_order(message):
  mcurs.execute("SELECT * FROM orders")
  result = mcurs.fetchall()
  if result == []:
    bot.send_message(message.chat.id, "No orders yet.", parse_mode='Markdown')
    return

  for i in range(len(result)):
    text = format_text(i + 1, result[i])
    bot.send_message(message.chat.id, text)


#Option 4 Branch: Updating Order Status
#Either update the ones u are delivering or cancel the ones you are ordering
@bot.message_handler(commands=['updateStatus'])
def update_status_reply(message):
  #Find out if they want check to cancel or check delivery
  bot.send_message(message.chat.id, '\n1. /updateDelivery \n2. /cancelOrders')


@bot.message_handler(commands=['updateDelivery'])
def update_Delivery_Orders(message):
  userID = message.from_user.username
  q = """SELECT * FROM orders WHERE Deliverer = ?"""
  mcurs.execute(q, (userID, ))
  myOrders = mcurs.fetchall()

  if myOrders == []:
    bot.send_message(message.chat.id, 'No current delivery orders')
  else:
    bot.send_message(
        message.chat.id,
        'You have ' + str(len(myOrders)) + ' Current delivery orders')
    for i in range(len(myOrders)):
      text = format_text(i + 1, myOrders[i])
      bot.send_message(message.chat.id, text)
    text = 'Enter which orderID you would like to update/cancel?'
    sent_msg = bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(sent_msg, updateDelivery)


def updateDelivery(message):
  possibleStatus = ['Not Taken', 'Taken', 'otw', 'arrived', "Completed"]

  q = """SELECT * FROM orders WHERE orderID = ?"""
  mcurs.execute(q, (message.text, ))
  r = mcurs.fetchone()
  a1 = 0
  if r:
    a1 = r[5]
    bot.send_message(message.chat.id,
                     'Change Status: \nFrom: ' + str(a1) + ' \nTo: ')
  bot.send_message(message.chat.id, '\n\nPlease Key in a number:')
  for i in range(len(possibleStatus)):
    bot.send_message(message.chat.id, str(i + 1) + ': ' + possibleStatus[i])
  bot.register_next_step_handler(message, updateQueryDelivery, ID=message.text)


def updateQueryDelivery(message, ID):
  possibleStatus = ['Not Taken', 'Taken', 'otw', "arrived", 'Completed']
  q = """SELECT * FROM orders WHERE orderID = ?"""
  mcurs.execute(q, (ID, ))
  r = mcurs.fetchone()
  if r:
    a = r[5]  #Status
    b = r[8]  #rID
    if a == possibleStatus[int(message.text) - 1]:
      bot.send_message(message.chat.id, 'Status already is that bozo')

    else:
      q = """UPDATE orders SET Status = ? WHERE orderID = ?"""
      mcurs.execute(q, (possibleStatus[int(message.text) - 1], ID))
      connection.commit()
      bot.send_message(message.chat.id, 'Status updated')
      try:
        text = 'Order has been updated by deliverer to: ' + possibleStatus[
            int(message.text) - 1]
        bot.send_message(b, text)
      except:
        pass


@bot.message_handler(commands=['cancelOrders'])
def cancel_orders(message):
  userID = message.from_user.username
  q = """SELECT * FROM orders WHERE Recipient = ? AND Status != 'purchased/otw'"""
  mcurs.execute(q, (userID, ))
  myOrders = mcurs.fetchall()

  if myOrders == []:
    bot.send_message(message.chat.id, 'No current orders')
  else:
    bot.send_message(message.chat.id,
                     'You have ' + str(len(myOrders)) + ' Current orders')
    for i in range(len(myOrders)):
      text = format_text(i + 1, myOrders[i])
      bot.send_message(message.chat.id, text)
    text = 'Enter which orderID you would like to cancel'
    sent_msg = bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(sent_msg, cancel_order_reply)


def cancel_order_reply(message):
  q = """SELECT * FROM orders WHERE orderID = ? AND rID = ?"""
  mcurs.execute(q, (message.text, message.from_user.id))
  d = mcurs.fetchall()
  bot.send_message(message.chat.id,
                   'do you really want to cancel? Y or N?',
                   parse_mode="Markdown")
  bot.register_next_step_handler(message, confirmation_reply, o=message.text)


def confirmation_reply(message, o):
  if (message.text == 'Yes'):
    q = """DELETE FROM orders WHERE orderID = ?"""
    qtwo = """SELECT * FROM orders WHERE orderID = ?"""
    r = mcurs.execute(qtwo, (o, ))
    row = mcurs.fetchone()
    c1 = None
    if row:
      c1 = row[7]
    if c1 != None:
      bot.send_message(c1, 'The recipiant has cancelled the order:\n')
    mcurs.execute(q, (o, ))
    connection.commit()
    bot.reply_to(message, 'Your order has been cancelled')
  else:
    bot.reply_to(message, 'Ok, order has NOT been cancelled.')


def ask_destination(
    message):  # TAKE DESTINATION ORDER AND INSERT INTO DATABASE
  temp_order_data.append(message.text.upper())
  rID = message.from_user.id
  username = message.from_user.username
  query = "INSERT INTO orders (Destination, Location, Food, Recipient, rID, Status) VALUES (?, ?, ?, ?, ?, ?)"
  mcurs.execute(query, (temp_order_data[2], temp_order_data[1],
                        temp_order_data[0], username, rID, "Not Taken"))
  connection.commit()

  bot.send_message(message.chat.id,
                   "Ok we got your order",
                   parse_mode="Markdown")

  temp_order_data.clear()


def ask_location(message):  # TAKE LOCATION ORDER AND INSERT INTO DATABASE
  temp_order_data.append(message.text)
  text = "Where would you like the food to be delivered to?"

  sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")

  bot.register_next_step_handler(sent_msg, ask_destination)


def ask_order(message):  # TAKE FOOD ORDER AND INSERT INTO DATABASE
  temp_order_data.append(message.text)
  text = "Where would you like the food to be bought from?"
  sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")

  bot.register_next_step_handler(message, ask_location)


#Order food
@bot.message_handler(commands=['order'])
def order_handler(message):
  text = "What food would you like to order?"
  sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
  bot.register_next_step_handler(sent_msg, ask_order)


# FOR DELIVERERS USAGE (SHOW ALL ORDER, CHOOSE ORDER(UPDATE ONCE CHOSEN), CANCEL ORDER)
def get_orders(
    message
):  # GET ALL ORDERS WITH DESIRED DESTINATION FROM DATABASE (SEND AS A MESSAGE)
  query = """SELECT * FROM orders WHERE Destination = ? AND Status = 'Not Taken'"""
  #   print(message)
  mcurs.execute(query, (message.text.upper(), ))
  output = mcurs.fetchall()
  # print(output)

  formatted = 'Which order would you like to deliver? (Input the ID) \n'
  if output == []:
    formatted += 'No orders found'
    return
  for tuple in output:
    id = tuple[0]
    location = tuple[1]
    destination = tuple[2]
    recepient = tuple[3]
    food = tuple[6]
    formatted += "ID %i, Location: %s, Destination: %s, Recepient: %s, Food: %s\n" % (
        id, location, destination, recepient, food)
  sent_msg = bot.send_message(message.chat.id,
                              formatted,
                              parse_mode="Markdown")
  bot.register_next_step_handler(sent_msg, choose_order)


def choose_order(message):  #CHOOSE ORDER FROM LIST OF ORDERS
  text2 = 'Order accepted, respond when food has been picked up'
  #UPDATE DATABASE
  updateQuery = """
        UPDATE orders
        SET Status = 'Taken', Deliverer = ?, dID = ?
        WHERE orderID = ? AND Status = 'Taken'
    """
  id = message.text
  mcurs.execute(updateQuery,
                (message.from_user.username, message.from_user.id, id))
  q = """SELECT * FROM orders WHERE orderID = ?"""
  mcurs.execute(q, (id, ))
  r = mcurs.fetchone()
  if r:
    a = r[5]  #Status
    b = r[8]  #rID
    bot.send_message(message.chat.id, 'Status updated')
    try:
      text = 'Order has been taken up by deliverer: ' + message.from_user.username
      bot.send_message(b, text)
    except:
      pass

  sent_msg = bot.send_message(message.chat.id, text2, parse_mode="Markdown")
  bot.register_next_step_handler(sent_msg, delivery_in_progress, id)


def delivery_in_progress(message, id):
  text2 = 'Input arrived when you have arrived'
  updateQuery = """
        UPDATE orders
        SET Status = 'otw'
        WHERE orderID = ? AND Status = 'otw'
    """
  mcurs.execute(updateQuery, (id, ))
  q = """SELECT * FROM orders WHERE orderID = ?"""
  mcurs.execute(q, (id, ))
  r = mcurs.fetchone()
  if r:
    a = r[5]  #Status
    b = r[8]  #rID
    bot.send_message(message.chat.id, 'Status updated')
    try:
      text = 'Order has been updated by deliverer: otw'
      bot.send_message(b, text)
    except:
      pass

  sent_msg = bot.send_message(message.chat.id, text2, parse_mode="Markdown")
  bot.register_next_step_handler(sent_msg, arrived, id)


def arrived(message, id):
  text2 = 'Please meetup with the recipient'
  updateQuery = """
        UPDATE orders
        SET Status = 'Arrived'
        WHERE orderID = ? AND Status = 'otw'
    """
  mcurs.execute(updateQuery, (id, ))
  connection.commit()

  q = """SELECT * FROM orders WHERE orderID = ?"""
  mcurs.execute(q, (id, ))
  r = mcurs.fetchone()
  if r:
    a = r[5]  #Status
    b = r[8]  #rID
    bot.send_message(message.chat.id, 'Status updated')
    try:
      text = 'Order has been updated by deliverer to: Arrived'
      bot.send_message(b, text)
    except:
      pass

  sent_msg = bot.send_message(message.chat.id, text2, parse_mode="Markdown")


@bot.message_handler(commands=['deliver'])
def delivery_lister(message):
  text = "Where do you want to deliver to? (CAPT, RC4, Tembusu, NUSC)"
  sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
  bot.register_next_step_handler(sent_msg, get_orders)


#Option to update status of orders you are delivering or cancel orders
@bot.message_handler(commands=['updateStatus'])
def checkOrder_lister(message):
  text = "Which order would you like to update?"
  sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
  bot.register_next_step_handler(sent_msg, get_orders)


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
  bot.reply_to(message, message.text)


bot.polling()
