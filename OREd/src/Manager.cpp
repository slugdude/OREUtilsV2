/**
 *  ORE Server management daemon
 *  Copyright (C) 2013 OpenRedstone
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "Manager.hpp"

namespace OREd
{
	bool Manager::OnCommand(Client* cli, const ArgsList& args)
	{
		HandlerMap::iterator it = m_Handlers.find(args[1]);

		if (it == m_Handlers.end())
		{
			return false; // Unknown command
		}

		return (it->second)(cli, args);
	}

	bool Manager::OnEvent(Client* cli, const ArgsList& args)
	{
		return true;
	}

	bool Manager::OnQuery(Client* cli, const ArgsList& args)
	{
		return true;
	}

	void Manager::InitConsole(const std::string& name, Console* console)
	{
		if (!console->IsValid())
		{
			return;
		}

		m_Consoles[name] = console;
	}

	Console* Manager::GetConsole(const std::string& name)
	{
		ConsoleMap::iterator it = m_Consoles.find(name);

		if (it == m_Consoles.end())
		{
			return NULL;
		}
		else
		{
			return it->second;
		}
	}
} /* OREd */
