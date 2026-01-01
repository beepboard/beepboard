require 'acrylic'
require 'sequel'

error_handler 400 do
    "Chandelier"
end

route do |conf, req|
    # runs before all other routes
    # connect to the database
    conf.database = Sequel.connect 'sqlite://data/beepboard.db'
end

route path: '/User/<id>', verb: :GET do |conf, req, id|
    id.to_s
end
