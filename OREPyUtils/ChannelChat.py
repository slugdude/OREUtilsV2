from collections import defaultdict

from Helper import Color, SendInfo, SendError, Colorify
import org.bukkit.Bukkit.getPlayer as getPlayer
import org.bukkit.Bukkit.getOnlinePlayers as getOnlinePlayers
import PersistentData

class ChannelMode:
	PUBLIC	 = 0
	PASSWORD = 1
	INVITE   = 2

class Channel:
	def __init__(self, node):
		self.mode    = int(node.mode)
		self.name    = str(node.name)
		self.players = []
		self.uuid = str(node.creator)
		self.invites = []
		self.pass = str(node.pass)

	def Join(self, player):
		if player in self.players:
			return False

		self.players.append(player)

		self.BroadcastJoin(player.getName())

		return True

	def Leave(self, player):
		if player not in self.players:
			return False

		self.players.remove(player)		

		self.BroadcastLeave(player.getName())

		return True

	def Broadcast(self, msg):
		for player in self.players:
			player.sendMessage(msg)

	def BroadcastMsg(self, playerName, chanMsg):
		msg = self.FormatPrefix() + Colorify(playerName) + ": " + Colorify(chanMsg)

		print("[CChat] "+self.name+'->'+playerName+': '+chanMsg)
		self.Broadcast(msg) 

	def BroadcastJoin(self, playerName):
		msg = self.FormatPrefix() + playerName + " has joined the channel"

		self.Broadcast(msg) 

	def BroadcastLeave(self, playerName):
		msg = self.FormatPrefix() + playerName + " has left the channel"
		self.Broadcast(msg)

	def Invite(self, player):
		self.invites.append(player)

	def FormatPrefix(self):
		return Color('b') + '[' + Color('8') + Color('o') + self.name + Color('r') + Color('b') + '] ' + Color('f')

class ChannelManager:
	MAX_CHANS = 10

	def LoadOrCreate(self):
		self.file = PersistentData.NodeFile("plugins/OREUtilsV2.py.dir/Data/Channels.json")
		self.node = self.file.node

		self.node.Ensure("ChannelManager")
		
		self.Channels = {}
		self.ChanNode = self.node.ChannelManager.Ensure("ChanNode")
		self.ActiveChannel = self.node.ChannelManager.Ensure("ActiveChannel")
		self.ActivePlayers = self.node.ChannelManager.Ensure("ActivePlayers")

		for chan in self.ChanNode:
			self.ChanNode[chan].Ensure("mode", ChannelMode.PUBLIC)
			self.ChanNode[chan].Ensure("name", str(chan))
			self.ChanNode[chan].Ensure("creator", '')
			self.ChanNode[chan].Ensure("pass", '')

			self.Channels[str(chan)] = Channel(self.ChanNode[chan])

		for player in getOnlinePlayers():
			if str(player.getUniqueId()) in self.ActiveChannel:
				print(player.getName())
				chan = self.GetOrCreate(player, self.ActiveChannel[str(player.getUniqueId())])
				self.Join(player, self.ActiveChannel[str(player.getUniqueId())], chan.pass)

	def Save(self):
		self.file.Dump()

	def GetOrCreate(self, sender, chanName):
		chan = self.Channels.get(str(chanName))
		
		if chan == None and sender != 0:
			if len(self.Channels) >= self.MAX_CHANS:
				return None
			
			self.ChanNode.Ensure(str(chanName))
			self.ChanNode[chanName].Ensure("mode", ChannelMode.PUBLIC)
			self.ChanNode[chanName].Ensure("name", str(chanName))
			self.ChanNode[chanName].Ensure("creator", str(sender.getUniqueId()))
			self.ChanNode[chanName].Ensure("pass", '')

			chan = Channel(self.ChanNode[str(chanName)])

			self.Channels[str(chanName)] = chan

		return chan

	def Join(self, player, chanName, pss=' '):
		chan = self.GetOrCreate(player, chanName)

		if chan == None:
			return False

		if chan.mode == ChannelMode.INVITE and player not in chan.invites:
			SendError(player, 'Channel is invite only!')
			return False
	
		if chan.mode == ChannelMode.PASSWORD and pss == ' ':
			SendError(player, 'Channel needs a password!')
			return False
		
		if chan.mode == ChannelMode.PASSWORD and pss != chan.pass:
			SendError(player, 'Incorrect password!')
			return False
		
		if not chan.Join(player):
			SendError(player, 'Already in channel')
			return False
	
		self.ActiveChannel[str(player.getUniqueId())] = chanName
	
		if chan.mode == ChannelMode.INVITE or player in chan.invites:
			del chan.invites[player]
		
		return True

	def Leave(self, player, chanName):
		chan = self.GetOrCreate(player, chanName)

		if chan == None:
			return False

		if not chan.Leave(player):
			return False

		if self.ActiveChannel[str(player.getUniqueId())] == chanName:
			del self.ActiveChannel[str(player.getUniqueId())]

		if not chan.players:
			del self.Channels[chanName]

		return True

	def ChanMsg(self, player, chanName, msg):
		chan = self.GetOrCreate(player, chanName)

		if chan == None:
			return False

		if player in chan.players:
			chan.BroadcastMsg(player.getName(), msg)
		
	def ChanMsgIRC(self, name, chanName, msg):
		chan = self.GetOrCreate(0, chanName)


		if chan == None:
			return False

		chan.BroadcastMsg(name, msg)

	def LeaveAll(self, player):
		for chan in self.Channels.itervalues():
			chan.Leave(player)

		if str(player.getUniqueId()) in self.ActiveChannel:
			del self.ActiveChannel[str(player.getUniqueId())]
		

Chans = ChannelManager()

def GetChan():
	return Chans

@hook.command("cchat", usage="/<command> <join|leave|info|switch> <channel> [pass]\n/<command> modify <channel> <PUBLIC|PASSWORD|INVITE> [pass]\n/<command> invite <channel> <user>")
def OnCommandCChat(sender, args):
	if len(args) < 2:
		return False

	cmd  = args[0]
	chan = args[1]

	if cmd == "join":
		if len(args) < 3:
			if Chans.Join(sender, chan, ' '):
				sender.sendMessage(Colorify("&8&oWelcome to channel " + Color('9') + chan))
		
		elif Chans.Join(sender, chan, args[2]):
			sender.sendMessage(Colorify("&8&oWelcome to channel " + Color("9") + chan))
		
		return True

	elif cmd == "leave":
		if Chans.Leave(sender, chan):
			sender.sendMessage(Colorify("&8&oYou have left the channel"))
		else:
			SendError(sender, "You are not in that channel")
		
		return True

	elif cmd == "info":
		if chan not in Chans.Channels:
			SendError(sender, "No such channel")
			return True

		msg = ', '.join([x.getName() for x in Chans.Channels[chan].players])

		sender.sendMessage(Colorify("&8&oPlayers in channel &9" + chan + ": &6" + msg))

		return True

	elif cmd == "switch":
		if chan not in Chans.Channels:
			SendError(sender, "No such channel")
			return True

		if sender not in Chans.Channels[chan].players:
			SendError(sender, "You are not in that channel")
			return True

		Chans.ActiveChannel[sender.getName()] = chan

		return True

	elif cmd == "modify":
		if chan not in Chans.Channels:
			SendError(sender, 'No such channels')
			return True

		if str(sender.getUniqueId()) != Chans.Channels[chan].uuid:
			SendError(sender, 'You are not owner of the channel!')
			return True

		if len(args) < 3:
			return False

		if args[2] == "PASSWORD":
			if len(args) < 4:
				SendError(sender, 'No password set!')
				return True
			
			Chans.Channels[chan].mode = ChannelMode.PASSWORD		
			Chans.Channels[chan].pass = args[3]
		elif args[2] == "INVITE":
			Chans.Channels[chan].mode = ChannelMode.INVITE
		elif args[2] == "PUBLIC":
			Chans.Channels[chan].mode = ChannelMode.PUBLIC
		else:
			SendError(sender, 'Error! Unrecongnized modify!')

		return True
	
	elif cmd == "invite":
		if len(args) < 3:
			return False
		
		if chan not in Chans.Channels:
			SendError('No such channel!')
			return True

		if sender not in Chans.Channels[chan].players:
			SendError('You have to be in the channel to send invites!')
			return True
		
		online = False
		for plyr in getOnlinePlayers():
			if plyr.getName() == args[2]:
				Chans.Channels[chan].Invite(plyr)
				plyr.sendMessage(Color('8')+'You have been invited to join chat channel '+Color('4')+chan)
				return True

		SendError(sender, 'Player not found!')
			
	return False

@hook.command("ccadmin", usage="/<command> <list|playerinfo|kick>")
def OnCommandCCAdmin(sender, args):
	if not sender.hasPermission("ore.cchat.admin"):
		SendError(sender, "No permission")
		return True

	if len(args) == 0:
		return False

	cmd = args[0]

	if cmd == "list":
		sender.sendMessage("Active channels:")

		for chan in Chans.Channels.iterkeys():
			sender.sendMessage(chan)

		return True

	elif cmd == "playerinfo":
		if len(args) != 2:
			SendError(sender, "Usage: /ccadmin playerinfo <player>")
			return True

		sender.sendMessage("Player " + args[1] + ":")

		for chanName, chan in Chans.Channels.iteritems():
			for player in chan.players:
				if player.getName() == args[1]:
					sender.sendMessage(chanName)

		return True

	elif cmd == "kick":
		if len(args) != 3:
			SendError(sender, "Usage: /ccadmin kick <player> <channel>")
			return True

		chan = Chans.Channels.get(args[2])

		if chan == None:
			SendError(sender, "No such channel")
			return True

		for player in chan.players:
			if player.getName() == args[1]:
				SendInfo(player, "You have been kicked from channel " + args[2])

				SendInfo(sender, "Kicked player " + args[1] + " from channel " + args[2])

				chan.Leave(player)

		return True

	return False

@hook.command("cc", usage="/<command> <message>")
def OnCommandCC(sender, args):
	msg = ' '.join(args)

	if str(sender.getUniqueId()) not in Chans.ActiveChannel:
		SendError(sender, "You are not in a channel")
		return True

	chan = Chans.ActiveChannel[str(sender.getUniqueId())]

	if str(sender.getUniqueId()) in Chans.ActivePlayers:
		sender.sendMessage(Colorify('&8&oNow chatting in public chat.'))
		del Chans.ActivePlayers[str(sender.getUniqueId())]
	else:
		sender.sendMessage(Colorify('&8&oNow chatting in channel &9'+chan))
		Chans.ActivePlayers.Ensure(str(sender.getUniqueId()))

	return True

@hook.event("player.PlayerQuitEvent", "monitor")
def OnEventQuit(event):
	Chans.LeaveAll(event.getPlayer())

@hook.event("player.PlayerChatEvent", "Monitor")
def onEventPlayerChat(event):
	if str(event.getPlayer().getUniqueId()) not in Chans.ActiveChannel:
		return True

	if str(event.getPlayer().getUniqueId()) not in Chans.ActivePlayers:
		return True

	Chans.ChanMsg(event.getPlayer(), Chans.ActiveChannel[str(event.getPlayer().getUniqueId())], event.getMessage())
	event.setCancelled(True)
	
@hook.event("player.PlayerJoinEvent", "Normal")
def joinPlayer(event):
	if str(event.getPlayer().getUniqueId()) in Chans.ActiveChannel:
		uuid = str(event.getPlayer().getUniqueId())
		Chans.GetOrCreate(event.getPlayer(), Chans.ActiveChannel[uuid]).Join(event.getPlayer())

def OnEnable():
	Chans.LoadOrCreate()

def OnDisable():
	Chans.Save()
