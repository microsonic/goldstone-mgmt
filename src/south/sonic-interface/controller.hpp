#ifndef __CONTROLLER_HPP__
#define __CONTROLLER_HPP__


#include <map>
#include <vector>
#include <sstream>

#include <libyang/Libyang.hpp>
#include <sysrepo-cpp/Sysrepo.hpp>
#include <sysrepo-cpp/Connection.hpp>
#include <sysrepo-cpp/Session.hpp>
#include <sysrepo-cpp/Xpath.hpp>

#include <iostream>
#include <unordered_map>
#include <json.hpp>

using json = nlohmann::json;

class SonicController : public sysrepo::Callback
{
  public:
    SonicController(sysrepo::S_Session& sess);
    ~SonicController();
    void loop();

    int module_change (sysrepo::S_Session, const char *, const char *,
                       sr_event_t, uint32_t, void *);
    int oper_get_items (sysrepo::S_Session, const char *, const char *, const char *,
                        uint32_t, libyang::S_Data_Node &, void *);
    void set_sonic_parameters (std::string mgmt_server, std::string port);

  private:
    sysrepo::S_Session m_sess;
    sysrepo::S_Subscribe m_subscribe;
    std::string mgmt_server;
    std::string port;
};

#endif // __CONTROLLER_HPP__
