#ifndef QPID_AMQP_0_10_HOLDER_H
#define QPID_AMQP_0_10_HOLDER_H

/*
 *
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 *
 */
#include "qpid/framing/Blob.h"
#include "apply.h"

namespace qpid {
namespace amqp_0_10 {

template <class DerivedHolder, class BaseHeld, size_t Size>
struct Holder : public framing::Blob<Size, BaseHeld> {

    typedef framing::Blob<Size, BaseHeld> Base;
    
    Holder() {}
    template <class T> Holder(const T& value) : Base(value) {}

    using Base::operator=;

    uint8_t getCode() const { return this->get()->getCode(); }
    uint8_t getClassCode() const { return this->get()->getClassCode(); }
    
    template <class S> void encode(S& s) {
        s(getClassCode())(getCode());
    }

    template <class S> void decode(S& s) {
        uint8_t code, classCode;
        s(classCode)(code);
        static_cast<DerivedHolder*>(this)->set(classCode, code);
    }

    template <class S> void serialize(S& s) {
        s.split(*this);
        apply(s, *this->get());
    }
};


}} // namespace qpid::amqp_0_10

#endif  /*!QPID_AMQP_0_10_HOLDER_H*/
