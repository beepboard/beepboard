require 'acrylic'

class Song < Acrylic::Kronos::Record
    record_version 1

    column :text, :name
end

Acrylic::Kronos::init

route path: '/User', verb: :GET do |conf, req|
end
